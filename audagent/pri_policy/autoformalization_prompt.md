I will give you a privacy policy written in natural language. Your task is to analyze this privacy policy and convert it into a structured formal representation.
The formal representation should capture each collected data type, along with its collection method, usage purpose, disclosure to which third parties (if any), and retention policy.
More specifically, please use the following schema:

```
{
  "types_of_data_collected": one data types collected, e.g., "personal_identifiable_information", "usage_data", "cookies",
  "methods_of_collection": the methods used to collect this data, e.g., "directly from users" or "indirectly through cookies or tracking technologies",
  "data_usage": purposes for which this data is used, e.g., "improving services", "personalization", "marketing",
  "third_party_disclosure": third parties with whom the data is shared, e.g., "service providers", "advertisers", "not disclosed to third parties",
  "retention_period": how long data is retained, e.g., "30 days", "until user deletes it",
}
```

Each data type should be represented as a separate object in a list. 
If certain information is not specified in the privacy policy, please indicate it as "not specified".
Please provide the formal representation in JSON format. Here is the privacy policy to analyze:

[Insert Privacy Policy Here]
