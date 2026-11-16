# Hosting options: course demo and portfolio

**Date:** 15 Nov 2026 (Singapore time)  
**Status:** Proposed design for team review; no hosting resources purchased or deployed.  
**Scope:** Local assessed demo first, hosted portfolio after the course.

## 1. Recommendation

Keep the course application on the demo laptop: React, the Python backend, MySQL and retrieval assets all run locally. Calls to the class-provided LLM endpoint still require connectivity. The [client brief](../00-Biz_Requirements/CLIENT_BRIEF.md) requires a working application and live demonstration; it does not require public hosting. This also matches the local deployment direction in [team plan v0.5, section 9](../01-Plans_Status/Capstone_TEAM_PLAN_v0.5.md).

After the course, retain React and the Python services and deploy a small portfolio edition on **Railway**. Start with two services: one application service serving the built React frontend and Python API, and one MySQL service with persistent storage. Use synthetic data, preprocessed evidence and separately authorised model credentials. Budget **USD 20–35/month for hosting as an initial planning allowance**, then revise from measured usage; model charges, backups, domain registration and taxes are additional.

This recommendation assumes low portfolio traffic and a named person willing to own billing and upkeep. Railway reduces server administration while retaining MySQL. If predictable infrastructure cost matters more than administration effort, use a **single DigitalOcean virtual server with Docker Compose** instead. If the budget is zero, publish a clearly labelled static sample experience and project case study; a complete, continuously available AI application with persistent MySQL should not depend on temporary free credits.

## 2. What changes between local and hosted use?

| Concern | Course: local laptop | Portfolio: hosted application |
| --- | --- | --- |
| Access | Presenter uses a local browser. | Visitors use a public HTTPS address independently of the laptop. |
| Frontend | Vite development server or locally served React build; Streamlit is also possible locally. | Serve a production React build, or run a persistent Streamlit Python service. |
| Backend | Python process on the laptop. | Hosted Python service with restart policy, health checks and request limits. |
| MySQL | Existing Docker service and named volume. | Hosted MySQL with its own persistent volume, credentials and recovery procedure. |
| Evidence and retrieval | Local images, extracted text and indexes. | Portfolio-safe assets packaged into a versioned build or durable hosted storage. |
| Model access | Class endpoint and course budget. | Independently permitted endpoint/key and an ongoing budget, or labelled sample mode. |
| Availability | Laptop must remain on; presenter controls startup. | Hosting account remains funded; monitor failures and renew credentials. |
| Data | Course package stays local and ignored by Git. | Fresh synthetic package with fictional identifiers, images, policies and evidence. |
| Cost | No new hosting bill; existing hardware and course API budget. | Compute, database/storage, transfer, model usage and optional domain/backups. |

`localhost` always means the machine running the process. A cloud backend configured with `localhost:3306` looks for MySQL inside its own runtime, not on the team's laptop. Hosting only the React frontend therefore does not host the working application. Keep database access and model credentials on the server.

## 3. React versus Streamlit

Framework choice and hosting choice are separate decisions. Both can run locally and both can be hosted.

| Aspect | React + Python API | Streamlit + Python services |
| --- | --- | --- |
| Course work | Existing React scaffold; requires API/UI integration. | Quick Python UI if the team chooses the fallback; replacing React introduces rework. |
| Hosted runtime | React compiles to static files; Python still needs server compute. Both can share one application service. | Python UI server remains running and calls shared service modules or a separate API. |
| MySQL | Access through the backend. | Access through server-side Python. |
| Portfolio experience | More control over layout, interactions and frontend engineering evidence. | Suitable for a data/AI demonstration with less frontend work. |
| Free frontend hosting | Possible, but covers only static assets. | Community Cloud hosts the Python UI, with its own resource and sleep constraints. |
| Reuse | Reuse the existing UI and backend contracts. | Reuse backend logic if it is independent of the UI framework. |

**Proposal:** keep React because the scaffold and work allocation already assume it. A later hosting requirement alone is not a reason to switch. If the team ultimately chooses Streamlit for delivery, the Railway or virtual-server options still work; substitute the Streamlit service for the combined React/API service. Streamlit supports server-side SQL connections and secrets configuration. [Streamlit connections documentation](https://docs.streamlit.io/develop/concepts/connections/connecting-to-data)

## 4. Hosting options compared

Prices are public USD list prices checked on 15 Nov 2026, not quotations. Recheck before purchasing. Planning allowances below are team estimates rather than provider promises.

| Option | How the complete application fits | Cost and operational tradeoffs | Assessment |
| --- | --- | --- | --- |
| **Local laptop** | React/Streamlit, backend, MySQL and files remain local. | No hosting fee; depends on laptop power, connectivity and manual startup. | **Course recommendation.** Insufficient for independently accessible portfolio use. |
| **Streamlit Community Cloud + external MySQL** | Streamlit UI and Python logic run in Community Cloud; MySQL must be hosted separately. | Community Cloud is free, but the database and model calls may cost money. Apps sleep after 12 hours without traffic; resource limits apply. [Cloud overview](https://docs.streamlit.io/deploy/streamlit-community-cloud), [sleep behaviour](https://docs.streamlit.io/deploy/streamlit-community-cloud/manage-your-app) | Good if Streamlit is already chosen and waking the app is acceptable. Does not provide the project's MySQL service. |
| **Static React hosting + separate API/MySQL** | GitHub Pages serves the React build; a separate provider runs Python and MySQL. | Public-repository Pages hosting is available on GitHub Free. Backend costs remain, with extra configuration for API URLs, allowed origins and cookies. [GitHub Pages](https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages) | Good for a permanent case study or sample UI. Optional later split for the live app; initially adds another deployment boundary. |
| **Railway application + MySQL** | Combined React/Python service, MySQL service and persistent volumes in one project. | Usage-based billing. Hobby has a USD 5 monthly minimum including USD 5 usage; Pro has a USD 20 minimum including USD 20 usage. Hobby is positioned for an individual; Pro supports team workspace needs. [Pricing](https://railway.com/pricing) | **Preferred portfolio start.** Low server administration; monitor actual cost and storage. |
| **Render application + MySQL** | React static site, Python web service and MySQL on a paid service with a persistent disk, or external MySQL. | Free web services sleep after 15 idle minutes and cannot attach persistent disks. Free Render Postgres expires after 30 days and would require changing database engine. Paid compute and storage are separate costs. [Free services](https://render.com/docs/free), [FAQ](https://render.com/docs/faq) | Viable paid alternative. Its free tier does not supply durable MySQL for this design. |
| **Single virtual server: DigitalOcean or AWS Lightsail** | Docker Compose runs a reverse proxy, application and MySQL on one server. | DigitalOcean Basic lists 2 GiB/1 vCPU at USD 12/month and 4 GiB/2 vCPU at USD 24/month. Backups and model usage add cost. Team maintains OS, firewall, TLS, database and recovery. [Droplet pricing](https://www.digitalocean.com/pricing/droplets) | Best alternative for a predictable base bill and infrastructure learning. Start sizing at 4 GiB as an estimate; measure before choosing. |
| **Separate compute + managed MySQL** | Application containers plus a database service such as Lightsail managed MySQL. | More components and a separate database bill. Lightsail advertises managed database plans from USD 15/month; its entry plan lists no data encryption, with encrypted plans from USD 30/month. Region affects pricing. [Lightsail pricing](https://aws.amazon.com/lightsail/pricing/), [supported engines](https://docs.aws.amazon.com/lightsail/latest/userguide/amazon-lightsail-databases.html) | Appropriate when database operations justify the extra spend. More than this small portfolio initially needs. |

Using PostgreSQL or SQLite could create other low-cost configurations, but would change SQL compatibility, migrations and evaluation coverage. Preserve MySQL initially to reduce migration work.

## 5. Proposed Railway portfolio design

These are target components, not claims about features already implemented.

| Component | Proposed arrangement |
| --- | --- |
| Public entry | Railway HTTPS domain; custom domain optional. Railway supports public HTTPS routing. [Public networking](https://docs.railway.com/networking/public-networking) |
| Application | Build React during the image build; Python serves the generated assets and `/api/` routes. Use one origin for simpler browser configuration. Keep API paths separate from React fallback routing. |
| Database | Pin a supported MySQL 8 version compatible with the application; connect over Railway private networking. Give only the application access through a restricted database account. [MySQL deployment](https://docs.railway.com/databases/mysql), [private networking](https://docs.railway.com/networking/private-networking) |
| Durable state | MySQL volume at its database data directory. Store sessions in MySQL, or explicitly configure a separate persistent store. An app restart must not erase sessions. |
| Evidence | Package small, immutable synthetic images/text/indexes in the release. Use a separate app volume or object storage if runtime writes are necessary. The database volume is not a shared app filesystem. [Volumes](https://docs.railway.com/volumes/reference) |
| Ingestion | Run OCR, extraction and index construction before publishing a versioned synthetic dataset. Keep heavy processing out of visitor requests. |
| Model service | Configure credentials as server secrets. Add request, token, concurrency and daily spend limits; reject further live calls when the application budget is exhausted. |
| Public sample mode | Offer curated fictional complaints with explicitly labelled saved results when live access is disabled. A saved response must never appear to be newly generated. |
| Recovery | Keep dataset rebuild instructions and independent database exports. Enable suitable platform backups and test restoration. Railway documents a division of platform and user responsibilities; deployment does not remove the need to verify backups and upgrades. [Database responsibilities](https://docs.railway.com/databases) |

Do not copy the local Compose settings unchanged into public hosting: the current file publishes port 3306 and uses the demonstration root password. Use private database access and fresh secrets for the hosted edition. For a virtual server, expose HTTPS through the reverse proxy and keep MySQL on the internal Docker network.

### Cost model and ownership

The **USD 20–35 monthly hosting allowance** assumes a small dataset, low traffic, precomputed extraction and one application instance. It is unmeasured. At Railway's published resource rates, an illustrative 30-day workload averaging 1.5 GB memory, 0.1 vCPU and 2 GB of volume storage across services is about USD 17.32 before transfer and extras. Hobby billing is the greater of the USD 5 minimum or metered usage, rather than USD 5 added to all usage. This example is arithmetic, not a capacity benchmark. [Railway rates](https://railway.com/pricing)

Add model usage, backup storage, taxes and any domain separately. A team workspace may require Pro, with its higher minimum. Choose one billing owner or a suitable team plan; do not share personal account credentials. Review metrics after a week, set billing alerts/platform limits, and retain application-level model limits independently of hosting limits. Limits that suspend services can make the demo unavailable.

For the virtual-server alternative, USD 24/month buys the cited 4 GiB base server; backups, model calls and administration remain additional. Neither this nor Railway's initial single-instance design provides high availability.

## 6. Implementation sequence

### During the course

1. Complete the local complaint flow and weekly analytics; prioritise grading requirements.
2. Keep database connection settings, model endpoint/key and evidence paths configurable. Never embed secrets in React or its build variables.
3. Keep ingestion, retrieval, citations and guardrails in Python modules independent of the UI.
4. Document local startup, shutdown, persistent storage and recovery. The local MySQL volume is persistence, not a backup.
5. Record dependencies and repeatable loads. Add production container packaging when the application stabilises; cloud provisioning is outside the course demo's critical path.
6. Rehearse with local data and the actual class endpoint. Handle endpoint/network failure honestly; local hosting does not make remote LLM calls work offline.

### After the course

1. Assign an owner, monthly budget and chosen hosting account. Confirm ongoing model access separately from the course key.
2. Create a complete fictional dataset covering SQL, tabular, GPS, document and image sources. Preserve ambiguity, conflicting timestamps and missing-evidence cases. Rebuild derived text/indexes from those synthetic sources.
3. Add a release image that serves React and the Python API; configure the platform port and health checks. Build for the host architecture rather than copying laptop binaries or a local virtual environment.
4. Provision the app and MySQL with durable storage, private connectivity and independent secrets. Load synthetic data through a repeatable command, not on every web request or replica startup.
5. Configure model limits, citation asset access, session isolation, concise logs and a clearly labelled sample fallback. Start with curated inputs; expand arbitrary input only with bounded resource use.
6. Verify from another device with the laptop switched off: complaint triage, ambiguity clarification, image citations, weekly counts, model failure and budget exhaustion.
7. Restart and redeploy the services; verify database/session persistence, restore a backup, and confirm the release contains no course package or class credentials.
8. Publish the portfolio URL with a short case study, architecture, evaluation results and known limitations. Review availability and cost monthly.

## 7. Decision to record

**Proposed:** local-only assessed demo; React retained; Railway for the post-course live portfolio; MySQL retained; synthetic data and separate model access; a single virtual server as the cost-predictability alternative; a static sample edition if recurring funding ends.

This document compares options and proposes a path. Final provisioning, the provider plan, ownership and spend remain team decisions after the course. It supplements the deployment direction in the team plan without introducing a hosting requirement for assessment.
