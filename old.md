# Note to Grader
One of the asks for the report was three samples for each intent supported, with a walkthrough of one of the samples, per intent.
That added a LOT of pages to my report.
I'm sorry about the length of the report, but I don't know how else to accomodate that ask.

# To Run Chatbot
1. Edit properties DB_URI, DB_USER, DB_PASS in: data_prep_scripts/cse_course_catalog/neo4j_load_database.py and chatbot/ir_nlg_cscatalog.py.
2. Install all libraries noted in requirements.txt.
3. Run data_prep_scripts/cse_course_catalog/neo4j_load_database.py to build the CS KG. !!!NOTE!!!: This will wipe your current Neo4j data.
4. Run debugserver.py.

# Final Project (Assignment 6)
For the final project you will be completing a chatbot that has skills for some
general tasks as well as skills related to the CSE courses. Your work so far
on the other assignments has been building up to this final project, now is the
time to assemble everything together and polish up your chatbot.

## The Base Chatbot (40 points)
With assignments 4 and 5 completed you should have a solid foundation for making
a chatbot, so in this part of the project you will be assembling everything
together and touching up any rough edges in the chatbot.

### Providing Responses (20 points)
In assignment 4 you explored how to interpret utterances and in assignment 5
you experimented with retrieving knowledge based on those utterances. In the
final project, all that's left is taking the retrieved knowledge, extracted
entities and intent, and formulating a natural language response.

For this part, you should improve your chatbot to now respond with natural
language for each of the intents from assignment 4.

Note: For the weather intent you can continue to "make up" the weather if you
are not querying an API. However, the responses must make it clear that the
weather value returned is trying to adhere to requests in the utterance. E.g.
Just returning something like "It will be cloudy with a 30% chance of rain." is
insufficient as we can't tell if the entities are properly interpreted. "The
weather in Seattle will be cloudy with a 30% chance of rain." would be
acceptable.

### Improving on Error Handling (20 points)
At this point, you should also improve the error handling so that the chatbot
communicates in natural language even when it cannot answer an utterance due to
lack of support or problems extracting sufficient amounts of entities to
formulate a response.

Some potential error cases to consider:
- Knowledge level: How to respond if the knowledge is not there, such as asking
    about a non-existant course or otherwise unanswerable query.
- Understanding level: How to respond if your chatbot did not fully understand
    the query (e.g. your NER failed to find enough necessary entities or if
    additional constraints were placed that your bot does not handle)
- Intent level: How to respond if you recognize but don't support an intent.

Note: You don't have to perfectly handle all these cases, though in the report
you should note at least 1 concrete case per category above and describe what
you implemented to deal with that case. Then given the implementation you
described, you should also discuss its hypothetical limitations (e.g. what other
cases in that category are not handled by your implementation, how well does
your implementation generalize to similar instances of that case).

## Report and Demo (30 points)
The evaluation of the chatbot in the final project is going to take a more
end-to-end approach and consist of a report and in-class demo. The demo sessions
will span 2 class sessions (6/8, 6/10). You will be assigned one breakout room
in one of the 2 sessions.

### What to include in your report (10 points)

You should include the following discussions or evaluations in your report:

- An overview of the design you ended up with, outlining each component and
    how you integrated the components. (E.g. Did you have multiple NER models,
    use semantic parsers, do topic extraction etc.) You _don't_ need to give
    specific internal details about things like tuning or training/eval, but you
    should cover all significant components (e.g. what models used for what,
    any manually written "rule-basde" logic used to handle certain things.)
    - Suggestion: Also providing a **flowchart diagram** for this part can be a
        really effective way to get yourself think about all the aspects of your
        bot design. Such a diagram is not mandatory but can make your overview
        much clearer and easier to write.
    - Note: For this part you also need to include any designs for "Choose your
        own project" part. You are reporting on the _final_ bot you have, not
        on just the base part.

- Demonstrative examples showing how your system would respond. We want to see:
    - At least 3 examples for each of the intents supported by your chatbot. (
        By default this is 6 but if you implemented any additional intents for
        the "custom" part of the chatbot, you must include examples for those
        too.)
    - If you are implementing multi-turn conversation, you need to include an
        example of a multi-turn conversation in each intent that supports it
        in addition to the individual examples.
    - A walkthrough of the procedure to respond for 1 example out of the ones
        you showcased. E.g. "The input sentence was (blah), which was first
        classified by the intent classifier as X. My chatbot then looked at the
        confidence (C) of the classifiction which was above the threshold T.
        The input was then routed to Y which extracted the entities E by doing
        (something) etc."

- ^ Error handling discussion from prev. part "Improving on Error Handling"
    (see that section for the requested discussion)

- ^ Custom improvements to your chatbot:
    - Indicate what custom options you picked
    - Based on each option you picked, provide the information required for that
        option (e.g. performance evaluation, )

^: Points for options marked with ^ are allocated to their corresponding
    sections rather than included as a part of the "Report and Demo" score.

### Preparing a Demo Video (20 points)
Since live demos span 2 days, to make it fair for everyone, you must record and
submit a video demo of your chatbot in action by the submission deadline before
the live presentation. (Most operating systems offer easy ways for you to
record your screen.)

This video should:
- Be no longer than _10 minutes_. Though we recommend staying within 5.
- Showcase at least 6 examples of utterances and responses for the base 
    chatbot (at least one for each of the 6 intents).
- Showcase at least 1 example of error handling for an unsupported intent.
- Showcase at least 2 examples for _each_ of your custom features. (E.g. if
    you improved knowledge base construction, showcase examples that utilizes
    the improved knowledge graph. )
    - If your feature needs to be shown in a contrastive way (e.g.
        personalization) every example being compared against each other counts
        as an individual example.

You should also include something that tells us what is what in the video:
- Option 1: You can provide a voiceover when recording the demo explaining
    each demo example. Your screen recording software may not support
    recording audio, in which case you would dub the audio on after the
    fact. We recommend OBS Studio if you want to go this route and don't 
	have screen recording software.
	- You can use a voice synthesis software to dub the video if you're not
	    comfortable recording your own voice.
- Option 2: You can provide a separate text file with timestamps and
    descriptions for each of the showcased items (e.g. 1:00 - "An example
    of the timer intent.")
	- Alternatively, we also accept subtitle files (SRT, SSA, ASS etc.) or
	   if you're going with the YouTube route (see end of document), you 
	   can use the built in closed-captions.

During the in-class live demo session you can showcase your system in any way
you think is fit---your goal for the demo is to try and get more votes. You 
should be prepared to accept and demo utterances suggested by your peers. The 
completeness of your system is judged mainly based on the submitted video with
5 points assigned to the in-class live demo participation.

Demos will be done during _class time_ with slots being assigned randomly and
released separately. If for some reason, you cannot make your assigned slot,
you can reach out to one of your peers and swap with them. If both sides agree
with a swap, one person can message us cc'ing the other. If you miss the
in-class demo, there will be a 5 point deduction to this portion + you won't be
eligible for the "peer voting extra credit" below.

### Extra Credit: Peer Voting (5 points)
Everyone will vote on the demos in their assigned breakout. Winners of the
popular vote in each breakout receive 3 points of EC (honorable mention).

At the end, winners in each breakout will demo to the entire class and everyone
will vote on the final winner, who will get 5 points of EC (best project).

Note: You shouldn't make any significant changes to your system after the video
demo submission. If features in your video demo are significantly different 
from those in the live demo, you may be disqualified for the extra credit. 

## Choose your own project (30 points, mix and match)
For this part you will have multiple options for features ranging from 10-30
points each. You can select which ones you want to implement or propose your
own.

Points for this section are stacked starting from the largest down to the
smallest. If the total points exceed 30, the _first_ overflow value will be
given as EC but not any others. (E.g. If you complete 2 x 10 and 1 x 15 you will
get 30 points on this section + 5 points of EC. If you complete 2 x 10 and
2 x 15, you will get 10 points of EC (15 + 15 + 10))

In your writeup and video demo, make sure to mention which option(s) you picked.

### Add a new skill: Alarms (10 points)
Implement a new skill that handles setting alarms or timers. The skill should
be able to extract the time or duration involved in the alarm. Like with the
weather intent, you don't actually need to create the alarm. However you should
indicate in the response that the parameters have been extracted (e.g. "OK,
I will set an alarm for Monday at noon.")

In the report you should provide an overview of your implementation including
what textual variations of utterances are supported and give a _qualitative_
evaluation of performance (quatitative evaluation is optional).

### Support a multi-turn conversation on a topic/intent (15 or 30 points)
Implement support for multiple turns on a conversation topic/intent. A
multi-turn exchange is one that _involves some working memory_ of the subjects
being discussed.

Example conversation:
```
"Can you recommend me a good restaurant around Y?"
"Sure. How about X?"
"Is there on street parking?"
"Yes. Though there are only limited spots available."
"Alright, can you give me their address."
"(...)"
```

Implement support for a multi-turn conversation on existing intents and/or a
new intent. Depending on what you implement this section may be worth different
amounts of points:
- Simple grounding: A simple implementation based on remembering past entities
    (over at least 2 turns) is worth 15 points.
- Query for missing information: An implementation that, in addition to
    remembering seen entities, can also actively query the user if required
    information is missing is worth 30 points. You should be able to gracefully
    handle multiple pieces of missing information and cases where the user
    indicates they can't supply the information.
- Sub-conversation support: Alternatively, supporting branching
    sub-conversations is also worth 30 points. In this case, in addition to
    remembering grouding information, you should be able to have contextual
    memory, i.e. your bot should be able to enter a sub-conversation and exit
    from it while maintaining separate contexts. Example:
    ```
    "What are the best Mexican food restaurants around?"
    "Based on reviews, X is the most highly rated in your proximity."
    "Can you tell me what people liked about X?" /* -> Enter sub conv */
    "(...)"
    "Do they have any specials right now?"
    "(...)"
    "Do you know if they have parking available?"
    "They only have limited on street parking available. "
    "Anything else further away then?" /* -> Exit sub conv */
    "What about restaurant Y? They are also well rated but 10 mins further away"
    ```
- (If you have any alternatives in mind for multi-turn conversation, use the
    proposal to propose them.)

Note: To handle topic changes you may need to resolve coreferences and decide
when to update in-memory items. This can be challenging, so we don't expect this
to be done perfectly---a decent attempt at some level of such support is ok as
long as you document your design and testing process well.

In both cases, you will need to document the details of your implementation (
what components, how were they assembled, etc.) as well as give a _qualitative_
evaluation of performance on some examples. If you're implementing complex
conversation rounds (anything 30 points), you should also give a more in-depth
discussion about the limitations you observe and anticipate (e.g. why do/would
they occur and what could be future paths to resolve them).

### Personalization / Multiple Users (15 points)
Implement support for personalization across multiple users. Each session
requested through the API should be isolated from each other and within each
session, your chatbot should keep track of some personalized information for
that session. This could be in the form of a user's name or the bot may use
a different tone of voice/wording depending on interactions with the user.

This personalized information must contribute to some aspect of the bot's
interactions with different users that is distinct. However you do not
necessarily need to enable updating this information during the chat. (E.g. you
might simulate a bot that "knows" different user's course histories and gives
advice by taking that into account.)

For the report, you should outline the code design for your personalization
implementation and provide a discussion about its performance.

One suggested combination is to implement personalization along with simple
multi-turn conversations, which will likely allow you to share some of the
implementation for tracking context while allowing it to be updated in chat.

### Support more complex knowledge graph queries (10 or 15 points)
Improve your knowledge graph and queries on it beyond the basic cases in
Assignment 5.

For this option you will need to do _one of_ the following:
- Support improved topic querying for the knowledge graph (should be able to
    index and ask about _course topics beyond the course name_.) (10 points)
- Better extraction of additional context in queries by supporting something
    other than just the entities (course ids, topics). For example, you could
    enable queries that constrain course level and topic together. (10 points)
- Implement a simple prerequisites planning system to handle queries like
    "If I've already taken X and want to take a graduate level class on topic Y,
    which classes should I take next?" (15 points)

(Note: If you do more than 1 of the above, only the highest point one will
count.)

Implement the improved knowledge base queries (including any necessary changes
to the schema and data extraction to populate the knowledge base). Outline your
design in the report (including any schema changes if you needed to make them)
and provide examples showing the improvements compared to the base design. It
may be hard to show this end-to-end, so feel free to provide info like showing
better queries being generated internally.

### Incorporate emotion in response (10 points)
Make your bot's responses more human by incorporating emotion variation in how
the bot responds. You can use a sentiment analysis model to try and understand
the user's emotional tone and based on the user's emotions should incorporate
variation in how your bot responds.

Outline the design in the report (including performance metrics for sentiment
analysis). Provide examples that showcase how responses vary depending on
differing sentiment of the users' utterances.

### Propose your own feature (Variable)
You can also propose your own feature for this part. There will be a proposal
period for custom features/improvements (separately annnounced).

During this period, if you want to propose a feature, make a public post on Ed
tagged with "A6 - Proposal".

If you see someone else's proposal that you would like to implement as-is, use
the like feature to upvote it. However, if you only like parts of the proposal
but not everything, you should start a new proposal instead. All proposals will
be considered by the staff regardless of the amounts of votes, though we may
decide to combine proposals that are similar.

Once the proposal period ends, we will assess each proposal and assign a point
value to it. These will then be posted on Ed and offered to anyone as additional
choices for the custom features. Points are assigned based on the expected level
of effort required.

Proposals can be assigned one of the following point values:
- 0 points - Proposal not accepted. Indicated feature is already covered by the
    base chatbot, prior assignment ECs, or is below the amount of effort
    required (either the feature itself or the proposed evaluation).
- 10 points
- 15 points
- 30 points

We will also indicate any mutually exclusive options (likely because they have
too much overlap). If multiple mutually exclusive options are done, only the
highest point one will be considered.

Note: To propose a new feature, you need to outline both the feature itself and
how you plan to present and evaluate the feature. During the proposal period, we
may also give suggestions for the presentation and evaluation proposed if the
propsed version seems insufficient.

## What to submit
In your final repo you should include the following:

- A final report  `final_report.pdf` (see above)
- A video demo. This can either be a video file uploaded to _Canvas_ or you can
    provide a link to an unlisted YouTube video. If you chose to provide
    timestamps, also make sure to include that in the submission.
    - If opting for the Youtube option, you can use built-in subtitles or
        timestamp functionality instead of providing a text file to show us
        the timestamps.
- Your codebase checked into Gitlab. The code doesn't need to work
    "out-of-the-box" but if it requires additional manual setup, you should
    include reasonable instructions/documentation.
