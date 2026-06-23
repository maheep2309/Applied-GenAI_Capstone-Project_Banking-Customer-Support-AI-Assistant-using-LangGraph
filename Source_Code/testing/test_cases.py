
# ==========================================================
# Create Test Cases For Classifier Evaluation
# ==========================================================

CLASSIFIER_TEST_CASES = [

# -----------------
# POSITIVE (10)
# -----------------

{
    "category": "Positive",
    "query": "Thank you for resolving my issue.",
    "expected_intent": "positive"
},

{
    "category": "Positive",
    "query": "Everything is working now.",
    "expected_intent": "positive"
},

{
    "category": "Positive",
    "query": "The problem is fixed now.",
    "expected_intent": "positive"
},

{
    "category": "Positive",
    "query": "You may close the ticket.",
    "expected_intent": "positive"
},

{
    "category": "Positive",
    "query": "No further assistance is required.",
    "expected_intent": "positive"
},

{
    "category": "Positive",
    "query": "Great support, thanks.",
    "expected_intent": "positive"
},

{
    "category": "Positive",
    "query": "Appreciate your help.",
    "expected_intent": "positive"
},

{
    "category": "Positive",
    "query": "Thank you for the update.",
    "expected_intent": "positive"
},

{
    "category": "Positive",
    "query": "Got it, thanks.",
    "expected_intent": "positive"
},

{
    "category": "Positive",
    "query": "I am satisfied with the resolution.",
    "expected_intent": "positive"
},

# -----------------
# NEGATIVE (10)
# -----------------

{
    "category": "Negative",
    "query": "My issue is still not fixed.",
    "expected_intent": "negative"
},

{
    "category": "Negative",
    "query": "The card has still not arrived.",
    "expected_intent": "negative"
},

{
    "category": "Negative",
    "query": "The problem has started again.",
    "expected_intent": "negative"
},

{
    "category": "Negative",
    "query": "I am unhappy with the resolution.",
    "expected_intent": "negative"
},

{
    "category": "Negative",
    "query": "The issue keeps happening.",
    "expected_intent": "negative"
},

{
    "category": "Negative",
    "query": "The issue still persists.",
    "expected_intent": "negative"
},

{
    "category": "Negative",
    "query": "The problem came back yesterday.",
    "expected_intent": "negative"
},

{
    "category": "Negative",
    "query": "Support has not solved my issue.",
    "expected_intent": "negative"
},

{
    "category": "Negative",
    "query": "The issue remains unresolved.",
    "expected_intent": "negative"
},

{
    "category": "Negative",
    "query": "The replacement card has not arrived yet.",
    "expected_intent": "negative"
},

# -----------------
# INQUIRY (10)
# -----------------

{
    "category": "Inquiry",
    "query": "What is the status of my INC0000000001?",
    "expected_intent": "inquiry"
},

{
    "category": "Inquiry",
    "query": "Can you provide an update on INC0000000006?",
    "expected_intent": "inquiry"
},

{
    "category": "Inquiry",
    "query": "Has my issue been resolved for the ticket id INC0000000010?",
    "expected_intent": "inquiry"
},

{
    "category": "Inquiry",
    "query": "When will INC0000000015 be fixed?",
    "expected_intent": "inquiry"
},

{
    "category": "Inquiry",
    "query": "Please check my ticket INC0000000017.",
    "expected_intent": "inquiry"
},

{
    "category": "Inquiry",
    "query": "Is there any progress on the investigation related INC0000000013?",
    "expected_intent": "inquiry"
},

{
    "category": "Inquiry",
    "query": "Can you tell me the current status of INC0000000019?",
    "expected_intent": "inquiry"
},

{
    "category": "Inquiry",
    "query": "Any update on my case INC0000000011?",
    "expected_intent": "inquiry"
},

{
    "category": "Inquiry",
    "query": "When will this ticket INC0000000008 be closed?",
    "expected_intent": "inquiry"
},

{
    "category": "Inquiry",
    "query": "Could you check the progress on my complaint INC0000000020?",
    "expected_intent": "inquiry"
}

]