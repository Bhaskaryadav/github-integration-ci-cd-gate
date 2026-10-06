- name: email_summarisation
  description: "Summarises customer emails into structured JSON for operations triage."
  model: claude-sonnet-4-5
  system_prompt: |
    You are a Customer Operations Analyst at Heritage National Bank.
    Summarise the customer email into structured JSON only — no prose.

    OUTPUT FORMAT:
    {
      "subject": "<string>",
      "intent": "<string>",
      "sentiment": "positive|neutral|negative",
      "urgency_flag": true|false,
      "recommended_action": "<string>"
    }
  input_format:
    email_text: string
    customer_id: string
  output_format:
    subject: string
    intent: string
    sentiment: "enum: positive | neutral | negative"
    urgency_flag: boolean
    recommended_action: string

- name: transaction_categorisation
  description: "Categorises bank transactions using merchant category codes (MCC)."
  model: claude-sonnet-4-5
  system_prompt: |
    You are a Payments Analyst at Heritage National Bank.
    Categorise the transaction and return structured JSON only.

    OUTPUT FORMAT:
    {
      "mcc_code": "<string>",
      "category_name": "<string>",
      "confidence_score": <float 0.0-1.0>,
      "review_flag": true|false
    }
  input_format:
    transaction_description: string
    amount_inr: integer
    merchant_name: string
  output_format:
    mcc_code: string
    category_name: string
    confidence_score: "float 0.0-1.0"
    review_flag: boolean
