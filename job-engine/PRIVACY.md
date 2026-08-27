# Job Opportunity Engine privacy boundary

The public Build Lab may contain architecture, scoring definitions, synthetic examples, and reusable code. It must not contain David's private job-search preferences, application history, saved-role digests, tailored answers, contact details beyond already public professional information, or automated application credentials.

A scheduled implementation must use a private repository or another private system of record. It may collect approved public job feeds, normalize and deduplicate roles, score them against private criteria, and prepare a private review digest. It must never submit applications, accept legal attestations, or publish the digest automatically.
