# Negotiator Implementation Steps

| Step | Title & Goal | New Code / Refactor | Demo & Tests |
|------|-------------|---------------------|--------------|
| 1 | User‑Needs Collector | • Minimal User Manager<br>• Stub Messenger (stdin/stdout)<br>• JSON writer | **Demo:** Run chat, show user_info.json<br>**Tests:** 1 happy‑path test that mocking input() yields expected JSON |
| 2 | Guide Opener Prototype | • Basic Guide Manager<br>• Append to chats/guideA.jsonl<br>• Skeleton Orchestrator calling User then Guide | **Demo:** Opener stored in chat log<br>**Tests:** Assert opener line exists, includes activity & date |
| 3 | Single‑Guide Round‑Trip | • Messenger stub feeds scripted reply<br>• Guide Manager logs inbound<br>• Atomic append | **Demo:** Outbound & inbound messages in log<br>**Tests:** Chat log has 2 lines; second sender == guide |
| 4 | Guide Info Extractor | • Price extractor in Guide Manager<br>• Write guide_info.json | **Demo:** Price captured in JSON<br>**Tests:** Assert JSON file exists and final_price_total == mocked amount |
| 5 | Minimal Negotiation | • Budget‑aware counter‑offer<br>• Guide refusal scripted | **Demo:** Counter message logged<br>**Tests:** Opener + counter lines present when budget set |
| 6 | Two‑Guide Anchor Logic | • Shared state; anchor negotiation<br>• Second Guide Manager | **Demo:** Second guide receives anchor price<br>**Tests:** Assert second opener mentions lower anchor figure |
| 7 | Report v1 | • Jinja2 template<br>• Manual session finish flag | **Demo:** Plain‑text report printed<br>**Tests:** Report contains two guide names + prices |
| 8 | Follow‑Up & Deadline | • Follow‑up scheduler via config<br>• Deadline termination<br>• Status "unresponsive" | **Demo:** Auto reminders then status update<br>**Tests:** After simulated time advance, follow‑up count == 3 |
| 9 | User Clarification Loop | • User Manager asks question from guide<br>• Update user_info.json | **Demo:** Guide asks "pickup?" user answers → reflected<br>**Tests:** Modified JSON contains "pickup": true |
| 10 | Recommendation & Notifications | • Recommendation logic<br>• Winner/loser messages | **Demo:** Report + polite decline sent<br>**Tests:** Loser chat log ends with decline template |
| 11 | CI Smoke Harness | • GitHub Actions workflow<br>• Add pytest -q gate | **Demo:** CI badge green<br>**Tests:** Existing suite runs in CI |
| 12 | Integration with Real LLM | • Messenger stub calls OpenAI for guide replies<br>• simulation_mode toggle | **Demo:** Live negotiation with LLM guides<br>**Tests:** Mark as slow; assert report still generates without crash |
