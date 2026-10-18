# End-to-end check: Ask over teammates' documents (E6)

This is the one check the unit tests, Postman folders and `verify` runs cannot do: two real people, real embeddings, a real central and Bedrock, and the real UI. It also settles two open items from earlier stories:

- **E6-S5:** a full-size 100-chunk upload batch through API Gateway (`long-handbook.txt` makes exactly 3 batches of 100).
- **E6-S6:** the full path (publish, teammate answer, edit sync, delete sync) with real 384-dimension embeddings.

## What you need

- **Two people**, each with their own HiveMind agent and sign-in. Use two laptops, or two Windows user accounts. Two agents on one Windows account share one credential-store entry and would act as the same user.
- Both on the **same team** (one creates it, the other joins with the invite code).
- On each machine, `agent/.env` with `HIVEMIND_COGNITO_CLIENT_ID`, `HIVEMIND_CENTRAL_API_URL` and the AWS credentials for Bedrock, and **no** `HIVEMIND_FAKE_EMBEDDINGS`. The first real search downloads the embedding model once (needs normal internet access).
- This branch checked out on both (agent and frontend), agent running on `127.0.0.1:8420`, frontend on `http://localhost:5173`.

Call the two people **A** (the owner) and **B** (the asker).

## Fixtures (`docs/e2e/fixtures/`)

| File | Chunks | Used for |
|---|---|---|
| `falcon-budget.txt` | 5 | The distinctive fact: the approved Falcon budget is **$48,200**, approved **14 September 2026**. |
| `long-handbook.txt` | 300 | Three upload batches. Fact in the first batch: the kitchen fridge is emptied **Friday at 4 pm**. Fact in the last batch: the guest wifi passphrase rotates **Thursday at noon**. |

## Steps

Tick each as you go, and note anything surprising.

1. **Publish (A).** A adds the `fixtures` folder on the Files page and waits for both files to be read. A makes both files public (the confirm now says teammates can read the contents, including through Ask).
2. **Chunks reached central.** Copy `docs/e2e/.env.example` to `docs/e2e/.env` (gitignored) and put A's HiveMind email and password in it. The Cognito client id and central API URL are read from `agent/.env`. Then run `python docs/e2e/mine.py` (or pass another env file, e.g. `python docs/e2e/mine.py b.env`). Expect about `5` chunks for `falcon-budget.txt` and `300` for `long-handbook.txt`.
   - 300 chunks means three batches of 100 went through, including the full-size batch (closes the S5 caveat).
3. **Owner goes offline (A).** A stops their agent (or closes the laptop).
4. **Ask (B).** On the Ask page B turns on "Also use teammates' public files" and asks:
   - "What is the approved Falcon project budget?" Expect **$48,200**, a source `falcon-budget.txt` marked **Teammate** with a **Download** button, and no note under the answer.
   - "When does the Harborview guest wifi passphrase rotate?" Expect **Thursday at noon** (from the last batch).
   - "When is the kitchen fridge emptied?" Expect **Friday at 4 pm** (from the first batch).
5. **Download with the owner offline (B).** B clicks Download on a teammate source. Expect "The owner just went offline." (or the owner-offline failure text), not a crash.
6. **Download with the owner online.** A restarts their agent and waits for it to connect. B clicks Download again. Expect the file in B's Downloads folder (`Saved to ...` shows the path).
7. **Narrowed scope (B).** With the switch on, B picks specific files in "Using all your files". Expect the hint "Teammates' files are only used when you haven't picked specific files." before sending, and after sending a note that teammates' files weren't used. The answer uses only B's picks.
8. **Switch off (B).** Turn the switch off and ask the Falcon question again. Expect no teammate source.
9. **Edit sync (A).** A edits `falcon-budget.txt` (change `$48,200` to `$52,900`), saves, and clicks Rescan on that folder. After a minute, `mine.py` still shows the file, and B asking the Falcon question gets **$52,900**, never the old figure.
10. **Delete sync (A).** A removes `falcon-budget.txt` from HiveMind (or deletes it from disk and rescans). After a minute, `mine.py` no longer lists it, and B asking the Falcon question gets no teammate source for it.
11. **Search regression (B).** On the Search page, tick "Also search teammates' public files", search for `handbook`, and download `long-handbook.txt` from the result card. This exercises the download control that Search and Ask now share.
12. **Cleanup.** A and B leave the team, A removes the fixtures folder from HiveMind, and `mine.py` shows nothing left.

## Recording the result

Paste what happened (pass or fail per step, and anything odd) into `docs/stories/e6-team-ask/E6-S7-frontend-and-e2e.md` under Notes. If everything passes, also tick the open items in the E6-S5 and E6-S6 story notes.
