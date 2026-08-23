# AI Critique

AI helped create many contract, input, state, and security test cases. However, its first results could not be trusted without human review.

For Pool A, AI assumed rules for OTP expiry and rate limits that were not clearly defined. It also created some wrong request bodies, used variables that had no value, and checked only the HTTP status in many tests. For Pool B, AI marked some boundary values incorrectly, created long decimal values by mistake, and left some repeated test ideas in the final list. For Pool C, AI misunderstood some order status rules. It also created tests that could pass even when the API changed an order incorrectly.

AI sometimes made bug claims that were too broad. For example, it claimed that many invalid-password cases consumed the reset token, but only API-080 clearly showed this behavior. This happened because AI often produced an answer that looked complete without clearly separating facts from assumptions.

Human review made the work more reliable. The test cases were checked against the requirements, repeated cases were removed, test data was reset before execution, and the full Newman suite was run. Database and order state were also checked when an HTTP response was not enough.

The main lesson is that AI is useful for suggesting test ideas and writing first drafts. A human must still confirm the requirements, expected results, and bug evidence. Every important claim should link to a requirement or a repeatable test result.
