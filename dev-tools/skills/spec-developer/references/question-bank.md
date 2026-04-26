# Question Bank

Organized by category. Each question includes insight notes (why it matters) and follow-up triggers (when to dig deeper). Select 3-4 per round, adapt based on previous answers.

---

## 1. Goals & Motivation

**Q1.1**: What specific problem does this feature solve, and what happens if we never build it?
- *Why*: Forces articulation of the real pain point vs. nice-to-have. If the "don't build" scenario is acceptable, the feature may not be worth speccing.
- *Follow-up if*: Answer is vague -> "Who experiences this pain, and how often?"

**Q1.2**: What does success look like 3 months after launch? How would you measure it?
- *Why*: Surfaces concrete acceptance criteria and KPIs. Prevents building something that can't be validated.
- *Follow-up if*: No measurable outcome -> "If we can't measure success, how will we know it's working?"

**Q1.3**: What existing workaround do people use today, and what's wrong with it?
- *Why*: Reveals the status quo baseline. The spec must improve on the current workaround, not just exist.
- *Follow-up if*: No workaround exists -> "So this is entirely new capability? What triggered the need now?"

**Q1.4**: Is there a deadline, external dependency, or event driving the timeline?
- *Why*: Surfaces hidden constraints that affect scope decisions. A hard deadline may mean MVP-first.
- *Follow-up if*: Yes -> "What's the minimum viable version that meets the deadline?"

---

## 2. Users & Actors

**Q2.1**: Who are the distinct user roles that interact with this feature, and what's different about each?
- *Why*: Prevents single-persona design. Different roles often need different flows, permissions, or views.
- *Follow-up if*: Only one role mentioned -> "Are there admins, operators, or automated systems that also interact?"

**Q2.2**: Walk me through a user's current workflow step by step -- what do they do before, during, and after this feature would be used?
- *Why*: Maps the full journey. Features often fail at handoff points between steps.
- *Follow-up if*: Steps are unclear -> "Where in this flow do they currently feel the most friction?"

**Q2.3**: What are users NOT telling you that you suspect is true? What assumptions are you making about their behavior?
- *Why*: Surfaces unstated assumptions. Often the spec author assumes behaviors that don't match reality.
- *Follow-up if*: "Nothing" -> "What's the riskiest assumption if it turned out to be wrong?"

**Q2.4**: How technically sophisticated are the users? What error messages or concepts can they handle?
- *Why*: Directly impacts error handling strategy, UI complexity, and documentation needs.
- *Follow-up if*: Mixed audience -> "Do power users and beginners need different paths?"

---

## 3. Data & State

**Q3.1**: What data entities does this feature create, read, update, or delete? List them explicitly.
- *Why*: Forces CRUD analysis. Missing entities = missing requirements.
- *Follow-up if*: Entities are unclear -> "What would the database tables or document schemas look like?"

**Q3.2**: What are the valid states and transitions for the core entity? Draw the state machine.
- *Why*: State machines reveal impossible transitions, missing states, and race conditions.
- *Follow-up if*: More than 4 states -> "What happens if the system crashes mid-transition?"

**Q3.3**: What data already exists in the system that this feature depends on? What if it's missing or malformed?
- *Why*: Existing data is never as clean as assumed. Migration and validation needs surface here.
- *Follow-up if*: Data quality is uncertain -> "Do we need a migration or data cleanup step first?"

**Q3.4**: What data needs to survive a system restart, and what can be ephemeral?
- *Why*: Distinguishes persistent storage needs from cache/session data. Affects architecture decisions.
- *Follow-up if*: Everything is persistent -> "What's the storage growth projection? Any retention/cleanup policy?"

**Q3.5**: Who owns this data? Are there privacy, retention, or regulatory constraints?
- *Why*: GDPR, HIPAA, data residency -- these constraints shape the entire data layer.
- *Follow-up if*: Personal data involved -> "What's the deletion/anonymization strategy?"

---

## 4. Behavior & Edge Cases

**Q4.1**: Describe the happy path end-to-end. Now: what's the first thing that could go wrong at each step?
- *Why*: Systematically generates failure modes. Each step's failure needs a defined response.
- *Follow-up if*: Failures are unclear -> "What if the input is valid but unexpected? Empty string, huge file, Unicode?"

**Q4.2**: What happens when two users do the same thing at the same time? Any concurrency concerns?
- *Why*: Concurrency bugs are the hardest to fix after launch. Spec must address locking, queuing, or conflict resolution.
- *Follow-up if*: Yes -> "Last-write-wins, optimistic locking, or merge strategy?"

**Q4.3**: What's the maximum realistic scale? Biggest input, most concurrent users, longest operation?
- *Why*: Scale extremes reveal architectural limits. A feature that works for 10 items may break at 10,000.
- *Follow-up if*: Large scale -> "Is pagination, batching, or async processing needed?"

**Q4.4**: What happens if this operation is interrupted halfway through? Partial state?
- *Why*: Idempotency and recovery are critical. Partial operations corrupt data silently.
- *Follow-up if*: Multi-step operation -> "Should it be transactional (all-or-nothing) or resumable?"

**Q4.5**: Are there any time-sensitive aspects? Timeouts, expiration, scheduled triggers?
- *Why*: Temporal behavior adds complexity. Timezone handling, clock skew, cron scheduling all need specification.
- *Follow-up if*: Yes -> "What happens when a deadline passes while the system is down?"

---

## 5. Error Handling & Recovery

**Q5.1**: How should errors be communicated to the user? What level of detail is appropriate?
- *Why*: Over-detailed errors leak internals. Under-detailed errors frustrate users. The balance is feature-specific.
- *Follow-up if*: Technical users -> "Should they see stack traces or structured error codes?"

**Q5.2**: When something fails, can the user retry, undo, or recover? How?
- *Why*: Recovery paths prevent support tickets. If there's no recovery, the error handling must be extra robust.
- *Follow-up if*: No recovery -> "Is there an admin override or manual fix path?"

**Q5.3**: What gets logged, and who looks at the logs? What alerts should fire?
- *Why*: Observability requirements are often forgotten until production. Log levels, structured logging, and alerting thresholds need definition.
- *Follow-up if*: No logging plan -> "How will you debug a production issue with this feature?"

**Q5.4**: What's the degraded-mode behavior? If a dependency is down, does this feature block entirely or gracefully degrade?
- *Why*: Total failure vs. partial functionality is a critical UX and architecture decision.
- *Follow-up if*: External dependencies -> "Is there a circuit breaker or fallback strategy?"

---

## 6. Integration & Dependencies

**Q6.1**: What existing systems, services, or APIs does this feature need to talk to?
- *Why*: Integration points are the #1 source of spec gaps. Each integration needs its own error handling.
- *Follow-up if*: External APIs -> "What are the rate limits, SLAs, and authentication methods?"

**Q6.2**: Does this feature expose an API or interface that other systems will consume?
- *Why*: API contracts are hard to change after consumers exist. Spec the contract before building.
- *Follow-up if*: Yes -> "Who are the consumers? What versioning strategy?"

**Q6.3**: What happens to this feature when a dependency is upgraded, deprecated, or removed?
- *Why*: Dependency lifecycle planning prevents future breakage. Tight coupling to a specific version is a risk.
- *Follow-up if*: Critical dependency -> "Is there an abstraction layer or alternative?"

**Q6.4**: Does this feature require data migration, schema changes, or backward compatibility with existing data?
- *Why*: Migration is often the riskiest part of a feature launch. Zero-downtime migration needs explicit planning.
- *Follow-up if*: Yes -> "Can we do rolling migration, or is a maintenance window needed?"

---

## 7. Constraints & Non-Functionals

**Q7.1**: What are the performance targets? Response time, throughput, resource limits?
- *Why*: Without targets, "fast enough" is undefinable. Concrete numbers enable testing.
- *Follow-up if*: No targets -> "What response time would make users complain?"

**Q7.2**: What are the security implications? Authentication, authorization, input validation, data exposure?
- *Why*: Security requirements shape the entire implementation. Bolt-on security doesn't work.
- *Follow-up if*: User-facing -> "What's the threat model? Who would attack this, and how?"

**Q7.3**: Are there accessibility, internationalization, or localization requirements?
- *Why*: A11y and i18n are expensive to retrofit. Must be planned from the start if needed.
- *Follow-up if*: Multiple locales -> "Which locales at launch? Is right-to-left needed?"

**Q7.4**: What are the testing requirements? Unit, integration, E2E, manual QA?
- *Why*: Testing strategy affects architecture (testability) and timeline. Define it in the spec.
- *Follow-up if*: Complex logic -> "Are there property-based testing or fuzzing needs?"

---

## 8. Non-Behaviors

**Q8.1**: What should this feature explicitly NOT do, even if it would seem "helpful"?
- *Why*: Prevents scope creep baked into the spec. Implementing agents fill gaps with plausible-but-wrong behavior.
- *Follow-up if*: No answer -> "If an agent implemented this and added [plausible nearby feature], would that be wrong?"

**Q8.2**: What behavior from a similar feature or library should this NOT inherit?
- *Why*: Systems often copy patterns from adjacent features. If that pattern is wrong here, the spec must say so.
- *Follow-up if*: Related features exist -> "Is there anything the old version did that the new one must stop doing?"

**Q8.3**: What would a "helpful" implementation add that would actually break existing workflows?
- *Why*: AI implementers optimize for completeness. Silent additions that break existing integrations are the hardest bugs.
- *Follow-up if*: Integration points exist -> "What would break if the system auto-formatted, auto-sorted, or auto-normalized this data?"

**Q8.4**: Are there any states, inputs, or requests this feature must reject, even if technically possible?
- *Why*: Explicit rejection rules prevent security by obscurity -- the system must refuse, not just not-do.
- *Follow-up if*: Yes -> "Is the rejection silent (returns empty) or explicit (returns an error)?"
