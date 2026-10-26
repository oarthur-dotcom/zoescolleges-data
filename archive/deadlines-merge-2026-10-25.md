# Deadlines merge, 2026-10-25 (batch 09 + Gemini extra + Muse round 3)

Inputs: meta-round3 (60), gemini-round3 (25), gemini-extra (33; the handoff said 34, the pasted file has 33), muse-round3 (50). 94 distinct schools.

## Rules used
- Dates all agree across sources except the ones listed below. Muse **X** verdicts win (exact quoted page text), as the handoff said.
- Gemini's "Y" is recorded as `year_check: reported`; Meta/Muse "Y" is `quoted`; "M" (page prints no year) is `none`. Where Gemini said Y but Meta/Muse said M on the same page, dates still agree, so the school stays and carries `reported`.
- Rounds that did not change are left byte-for-byte; only `checked` moves to 2026-10-25.
- New or changed rounds from an "M" verdict get `conf: medium`, so the app shows its existing "(some dates medium confidence)" note.
- Rolling-only schools with no dated round are not added (schema needs a date).
- Gemini-extra's second date field (notification) is ignored: it is inconsistent (some earlier than the deadline).
- **Gemini-extra had 7 rows with the wrong school id** (the URL belongs to a different school). Remapped by URL domain, used only as corroboration, and held when they disagree with live data. One (`sc-110635`, CSU system page filed under UC Berkeley) was dropped.

## Corrected by an X verdict (5)

- **Western Michigan University** (`sc-172699`): was [('EA', '2026-12-15')] -> now [('EA', '2026-12-01'), ('ROLLING', '2027-06-01')] [muse: Page heads "Fall 2027 entry": "Dec. 1, Early Action" and "June 1, Rolling Admission" — claimed Dec 15 EA is wrong (Dec 1]
- **University of Nebraska-Lincoln** (`sc-181464`): was [('RD', '2027-05-01')] -> now [('PRIORITY', '2026-11-01'), ('RD', '2027-05-01')] [muse: Page heads 'Fall 2027 Term': a 'November 1 Priority Deadline' round (for Feb 11 scholarship notification) is missing fro]
- **University of North Carolina Wilmington** (`sc-199218`): was [('EA', '2026-11-01'), ('RD', '2027-02-01')] -> now [('EA', '2026-11-01'), ('RD', '2027-01-15')] [muse: Admissions deadlines page: 'Fall Early Action (Non-Binding) - November 1,' decision ~January 20; 'Fall Regular Decision ]
- **Miami University-Oxford** (`sc-204024`): was [('EA', '2026-11-01'), ('ED1', '2026-11-01'), ('RD', '2027-02-01')] -> now [('EA', '2026-11-01'), ('EA2', '2026-12-01'), ('ED1', '2026-11-01'), ('RD', '2027-02-01')] [muse: Claim omits a round the page lists: Early Action II, Dec. 1 (notify Feb. 1); page shows Early Decision Nov. 1, Early Act]
- **Oklahoma State University-Main Campus** (`sc-207388`): Muse X: Current catalog states no application deadline (rolling admission); Nov. 1 is the 'Early Opportunity Scholarship Deadline,' not an application priority round

## Updated (3)

- **Calvin University** (`sc-169080`): was [('PRIORITY', '2027-01-31')] -> now [('PRIORITY', '2027-01-31'), ('RD', '2027-08-18')] [gx: Fall 2027 application deadline verified.]
- **University of North Dakota** (`sc-200280`): was [('PRIORITY', '2027-02-01')] -> now [('PRIORITY', '2027-02-01'), ('RD', '2027-08-15')] [meta: Feb1 priority Aug15 final no year]
- **University of Memphis** (`sc-220862`): was [('PRIORITY', '2027-07-01')] -> now [('RD', '2027-07-01')] [muse: Relabel: page prints Fall "Application Deadline" July 1 (file completion Aug 1), not a priority date — its only priority]

## New schools (9)

- **University of the Pacific** (`sc-120883`): reported; EA 2026-11-15, RD 2027-01-15
- **University of Northern Colorado** (`sc-127741`): reported; EA 2026-12-01, PRIORITY 2027-02-01, RD 2027-08-01
- **Delaware State University** (`sc-130934`): reported; EA 2026-11-02, RD 2027-04-15, ROLLING 2027-08-01
- **Lewis-Clark State College** (`sc-142328`): none; RD 2027-08-08
- **Columbia College Chicago** (`sc-144281`): reported; PRIORITY 2026-11-01
- **New York Institute of Technology** (`sc-194091`): reported; PRIORITY 2026-12-01
- **Neumann University** (`sc-214272`): reported; EA 2026-11-15
- **Johnson & Wales University-Providence** (`sc-217235`): reported; EA 2026-11-01, EA 2027-01-03, RD 2027-03-01
- **University of Wisconsin-Stout** (`sc-240417`): reported; PRIORITY 2027-01-01

## Held / kept as is -- needs Obie's call (7)

- **University of North Alabama** (`sc-101879`): North Alabama: Gemini-extra only says rolling (no dates) -- live Priority Mar 1 not re-verified.
- **Missouri State University-Springfield** (`sc-179566`): Missouri State-Springfield: Gemini-extra row carried the wrong id (IU-Bloomington). Says Priority Dec 1; live file has Priority Feb 1.
- **Long Island University** (`sc-192448`): LIU: Gemini-extra shows EA Dec 15 (+ED1 Nov 15, Priority Jan 5); live file has EA Dec 1. Its second-date fields are unreliable.
- **St. John's University-New York** (`sc-195809`): St. John's NY: Gemini-extra row carried the wrong id. Says EA Nov 1 / RD Jan 15; Meta + live file say EA Dec 1 / RD Feb 1.
- **Ohio University-Main Campus** (`sc-204857`): Ohio U: Muse reads the Feb 1 date as "Rolling Admission Deadline"; Meta + Gemini-r3 + live file call it RD. Kept RD.
- **University of South Carolina-Columbia** (`sc-218663`): USC Columbia: Gemini-extra row carried the wrong id. Says EA Nov 15 / RD May 1; live file has EA Oct 15 / RD Dec 1.
- **Winthrop University** (`sc-218964`): Winthrop: Gemini-extra lists a 2nd Priority (Feb 1); earlier Muse notes call Winthrop a relabel case.

## Not added (rolling, no dated round) (10)

- **Colorado Christian University** (`sc-126669`): rolling or no dated round: gx:Rolling admission policy confirmed.
- **Ringling College of Art and Design** (`sc-136774`): rolling or no dated round: gx:Rolling status verified.
- **Point University** (`sc-138868`): rolling or no dated round: gx:Rolling admissions policy verified.
- **Indiana University-Southeast** (`sc-151379`): rolling or no dated round: gx:Rolling admissions verified.
- **University of Maine at Augusta** (`sc-161217`): rolling or no dated round: gx:Preferred deadline listed without year.
- **Barton College** (`sc-197911`): rolling or no dated round: gx:Rolling admissions policy verified.
- **University of Mount Olive** (`sc-199069`): rolling or no dated round: gx:Rolling admissions policy verified.
- **DeSales University** (`sc-210739`): rolling or no dated round: gx:Rolling undergraduate admissions verified.
- **Norwich University** (`sc-230995`): rolling or no dated round: gx:Rolling admissions confirmed on official page.
- **ECPI University** (`sc-248934`): rolling or no dated round: muse:No claim on file; ECPI states it 'receives admissions applic

## Dropped rows (1)

- **University of California-Berkeley** (`sc-110635`): gx: no single catalog school (https://www.calstate.edu/attend/freshman)

## Re-verified, dates unchanged (55)

University of Alabama at Birmingham, Arizona State University Campus Immersion, University of California-Irvine, University of California-Santa Cruz, Pepperdine University, University of Colorado Denver/Anschutz Medical Campus, Fairfield University, University of Delaware, Georgia Southern University, University of Hawaii at Manoa, Boise State University, DePaul University, University of Illinois Chicago, Loyola University Chicago, Northern Illinois University, Ball State University, Indiana University-Indianapolis, University of Iowa, Eastern Kentucky University, University of Louisville, University of Louisiana at Lafayette, University of Maryland-Baltimore County, Towson University, University of Massachusetts-Boston, Oakland University, Wayne State University, University of Nevada-Reno, Rowan University, Montclair State University, CUNY Brooklyn College, CUNY City College, CUNY John Jay College of Criminal Justice, CUNY New York City College of Technology, CUNY Queens College, Fordham University, Rochester Institute of Technology, University at Buffalo, East Carolina University, University of North Carolina at Greensboro, Western Carolina University, University of Cincinnati-Main Campus, Kent State University at Kent, Clemson University, Coastal Carolina University, University of Houston-Downtown, Texas State University, Tarleton State University, The University of Texas at Dallas, The University of Texas at San Antonio, George Mason University, James Madison University, Washington State University, Florida Gulf Coast University, University of North Georgia, University of Maine

## Not in this PR
The earlier session's `deadlines-merged-20261025.json` (550 schools; 5 AIs) is not in this repo. This PR covers only the 4 verdict files above on top of the live 402-school file.
