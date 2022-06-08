import matplotlib.pyplot as plt
from sklearn.metrics import accuracy_score, classification_report
from torch.utils.data import DataLoader
from transformers import DistilBertTokenizerFast, DistilBertForSequenceClassification
from tqdm import tqdm
import torch
from torch.optim import Adam
import chatbot.tools as tools
import os

MODEL_NAME = 'models/chatbot_intent_classifier'
DEFAULT_HYPERPARAMETERS = {
    'optimizer': Adam,
    'learningRate': 5e-5,
    'numEpochs': 5
}

class IntentDataset(torch.utils.data.Dataset):
    def __init__(self, encodings, labels):
        self.encodings = encodings
        self.labels = labels

    def __getitem__(self, idx):
        item = {key: torch.tensor(val[idx]) for key, val in self.encodings.items()}
        item['labels'] = torch.tensor(self.labels[idx], dtype=torch.long)
        return item

    def __len__(self):
        length = len(self.encodings['input_ids'])
        return length

class IntentClassifier(object):
    def __init__(self, hyperparameters=DEFAULT_HYPERPARAMETERS, modelName=MODEL_NAME, plotLossAccuracy=False, evalTestData=False):
        # Basic object properties.
        self.hyperparameters = hyperparameters
        self.modelName = modelName
        self.plotLossAccuracy = plotLossAccuracy
        self.evalTestData = evalTestData
        #self.device = torch.device('cuda') if torch.cuda.is_available() else torch.device('cpu')
        self.device = torch.device('cpu')

        # Load the model and tokenizer.
        self.tokenizer = DistilBertTokenizerFast.from_pretrained("distilbert-base-uncased")
        self.model = self.__loadModel()

        # Record the indexed set of intent labels.
        _, train_labels = tools.read_data("train")
        self.classes = tools.labels(train_labels).tolist()
    
    def getIntent(self, query):
        self.model.eval()
        tQuery = self.tokenizer(query, truncation=True, padding=True)
        inputIds = torch.tensor([tQuery['input_ids']], dtype=torch.long).cpu()
        mask = torch.tensor([tQuery['attention_mask']], dtype=torch.long).cpu()
        outputs = self.model(inputIds, attention_mask=mask)
        sm = torch.nn.Softmax(dim=1)
        scores = sm(outputs.logits.cpu())
        iLabel = torch.max(scores, 1)
        label = self.classes[iLabel[1]]
        return label, iLabel[0].item()

    def evalOnTestData(self):
        # Prep the data.
        print("Reading raw data...")
        train_texts, train_labels = tools.read_data("train")
        test_texts, test_labels = tools.read_data("test")
        train_texts = train_texts.tolist()
        test_texts = test_texts.tolist()
        print("Converting labels...")
        classes = tools.labels(train_labels).tolist()
        train_labels = tools.relabel(train_labels, classes)
        test_labels = tools.relabel(test_labels, classes)
        print("Tokenizing data...")
        test_encodings = self.tokenizer(test_texts, truncation=True, padding=True)
        test_dataset = IntentDataset(test_encodings, test_labels)

        # Run the eval.
        print("Evaluating test data.")
        self.model.eval()
        self.model.to(self.device)
        test_loader = DataLoader(test_dataset, batch_size=16, shuffle=True)
        pred_labels, true_labels, _ = self.__validateEpoch(test_loader, self.model)
        self.model.cpu()
        report = classification_report(true_labels, pred_labels, labels=[i for i in range(len(classes))], target_names=classes)
        print(report)

    def __loadModel(self):
        model = None
        try:
            model = DistilBertForSequenceClassification.from_pretrained(self.modelName).cpu()
        except OSError:
            model = self.__trainNewModel(hyperparameters=self.hyperparameters, plotLossAccuracy=self.plotLossAccuracy, evalTestData=self.evalTestData, saveModel=self.modelName).cpu()
        model.eval()
        return model
    
    def __trainEpoch(self, dataloader, optimizer, model):
        # Initialize the labels and total loss; set the model to train mode.
        pred_labels = []
        true_labels = []
        tot_loss = 0.0
        model.train()

        # Loop through each batch to process
        for batch in tqdm(dataloader, total=len(dataloader), position=0, leave=True):
            # Save original labels for evaluation
            true_labels += batch['labels'].cpu().tolist()
            
            # Set device for everything in batch
            inputIds = batch['input_ids'].to(self.device)
            mask = batch['attention_mask'].to(self.device)
            labels = batch['labels'].to(self.device)
            
            # Forward and backward pass the model on the batch.
            optimizer.zero_grad()
            outputs = model(inputIds, attention_mask=mask, labels=labels)
            loss = outputs.loss
            loss.backward()
            optimizer.step()
            
            # Track the updated loss and the predicted labels.
            tot_loss += loss.item()
            pred_labels += torch.max(outputs.logits.cpu(), 1)[1].tolist()
            
        return pred_labels, true_labels, tot_loss / len(dataloader)

    def __validateEpoch(self, dataloader, model):
        # Init labels and loss; set model to eval mode.
        pred_labels = []
        true_labels = []
        tot_loss = 0.0
        model.eval()
        
        # Loop through each batch to process
        for batch in tqdm(dataloader, total=len(dataloader), position=0, leave=True):
            # Save original labels for evaluation
            true_labels += batch['labels'].cpu().tolist()
            
            # Set device for everything in batch
            inputIds = batch['input_ids'].to(self.device)
            mask = batch['attention_mask'].to(self.device)
            labels = batch['labels'].to(self.device)
            
            # Not compute gradients to save memory and speedup
            with torch.no_grad():
                # Feed items in batch into the forward pass
                outputs = model(inputIds, attention_mask=mask, labels=labels)
                
                # Record the loss and logits
                tot_loss += outputs.loss.item()
                pred_labels += torch.max(outputs.logits.cpu(), 1)[1].tolist()

        return pred_labels, true_labels, tot_loss / len(dataloader)

    def __trainNewModel(self, hyperparameters=None, plotLossAccuracy=False, evalTestData=False, saveModel=None):
        # Load Training Data
        print("Reading raw data...")
        train_texts, train_labels = tools.read_data("train")
        val_texts, val_labels = tools.read_data("val")
        test_texts, test_labels = tools.read_data("test")
        train_texts = train_texts.tolist()
        val_texts = val_texts.tolist()
        test_texts = test_texts.tolist()

        # Convert labels to ids.
        print("Converting labels...")
        classes = tools.labels(train_labels).tolist()
        train_labels = tools.relabel(train_labels, classes)
        val_labels = tools.relabel(val_labels, classes)
        test_labels = tools.relabel(test_labels, classes)

        # Tokenize the features and load intent datasets.
        print("Tokenizing data...")
        train_encodings = self.tokenizer(train_texts, truncation=True, padding=True)
        val_encodings = self.tokenizer(val_texts, truncation=True, padding=True)
        test_encodings = self.tokenizer(test_texts, truncation=True, padding=True)
        train_dataset = IntentDataset(train_encodings, train_labels)
        val_dataset = IntentDataset(val_encodings, val_labels)
        test_dataset = IntentDataset(test_encodings, test_labels)

        # Instantiate the raw model, fine tuning still required.
        print("Creating model...")
        num_labels = len(set(train_labels))
        model = DistilBertForSequenceClassification.from_pretrained('distilbert-base-uncased', num_labels=num_labels)

        # Define the training characteristics.
        model.to(self.device)
        if hyperparameters is None: hyperparameters = DEFAULT_HYPERPARAMETERS
        optimizer = hyperparameters['optimizer'](model.parameters(), lr=hyperparameters['learningRate'])
        batch_size = 16
        epoch_num = hyperparameters['numEpochs']
        train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
        val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=True)

        # Initialize loss and accuracy trackers.
        losses = {'train_loss':[], 'val_loss':[]}
        accuracies = {'train_acc':[], 'val_acc':[]}

        # Loop through each epoch: train, validate, then record the metrics.
        print("Beginning model fitting...")
        for epoch in range(epoch_num):
            print("Processing epoch %d of %d" % (epoch+1, epoch_num), flush=True)
            train_pred, train_labels, train_loss = self.__trainEpoch(train_loader, optimizer, model)
            val_pred, val_labels, val_loss = self.__validateEpoch(val_loader, model)
            train_acc = accuracy_score(train_labels, train_pred)
            val_acc = accuracy_score(val_labels, val_pred)
            accuracies['train_acc'].append(train_acc)
            losses['train_loss'].append(train_loss)
            accuracies['val_acc'].append(val_acc)
            losses['val_loss'].append(val_loss)
        print("Model fit complete!")

        print("Loss & Accuracy")
        print(losses)
        print(accuracies)

        # Plot out the loss and accuracy data.
        if plotLossAccuracy:
            print("Evaluating loss and accuracy.")

            # Plot the loss with respect to epoches
            plt.plot(losses['train_loss'], 'r--', label='train loss')
            plt.plot(losses['val_loss'], 'b', label='validation loss')
            plt.title("Loss wrt Epoch")
            plt.xlabel('Epoches')
            plt.ylabel('Loss')
            plt.legend(loc='upper right')
            plt.xticks([0, 1, 2], [1, 2, 3])
            plt.show()

            # Plot the accuricies with respect to epoches
            plt.plot(accuracies['train_acc'], 'r--', label='train accuracy')
            plt.plot(accuracies['val_acc'], 'b', label='validation accuracy')
            plt.title("Accuracy wrt Epoch")
            plt.xlabel('Epoches')
            plt.ylabel('Accuracy')
            plt.legend()
            plt.xticks([0, 1, 2], [1, 2, 3])
            plt.show()

        # Evaliate the test data. Only perform this operation when model training has been completed!
        if evalTestData:
            print("Evaluating test data.")
            test_loader = DataLoader(test_dataset, batch_size=16, shuffle=True)
            pred_labels, true_labels, _ = self.__validateEpoch(test_loader, model)
            # Compute evaluate report
            report = classification_report(true_labels, pred_labels, labels=[i for i in range(len(classes))], target_names=classes)
            print(report)

        # Save the model, if required.
        if saveModel:
            print("Saving model as %s" % (saveModel))
            model.save_pretrained(saveModel)

        return model