here’s a tight set of **YouTrack** docs you’ll need to implement MCP server.

# Core REST API + auth

* **REST API overview.** What the API covers, tooling, and client libs. ([JetBrains][1])
* **Base URL & endpoints.** How to form `/api/...` calls (plus custom endpoints, if you ever need them). ([JetBrains][2])
* **Auth with permanent tokens.** How to create and use a token (`Authorization: Bearer <perm token>`). ([JetBrains][3])

# Issues: search, create, update

* **Search/list issues** (`GET /api/issues?query=...`). Includes notes on default sorting and limits. ([JetBrains][4])
* **Query syntax for the `query` param** (same language as UI search). ([JetBrains][5])
* **Create an issue** (how-to, with project lookup first). ([JetBrains][6])
* **Issue entity reference** (fields, how `fields=` works in responses). ([JetBrains][4])
* **Update issue** (reference request; see linked docs from the Postman page). ([Postman][7])

# Duplicates & linking

* **Issue links (per-issue endpoints)** — read/add links. You’ll use this to mark **duplicates**. ([JetBrains][8])
* **Issue link types** (find the ID/name for *duplicates / is duplicated by*). ([JetBrains][9])

# Comments & attachments

* **Comments** (list/add/update). ([JetBrains][10])
* **Attachments** (upload files to an issue + step-by-step). ([JetBrains][11])

# Useful API mechanics

* **`fields` parameter** (request only what you need). ([JetBrains][12])
* **Pagination** (`skip`, `top`) and why you’ll see “42” results by default. ([JetBrains][13])

# Ready-made requests (handy while testing)

* **Official Postman collection** maintained by JetBrains (browse endpoints, copy cURL). ([Postman][14])


[1]: https://www.jetbrains.com/help/youtrack/devportal/youtrack-rest-api.html "YouTrack REST API | Developer Portal for YouTrack and Hub"
[2]: https://www.jetbrains.com/help/youtrack/devportal/api-url-and-endpoints.html "REST API URL and Endpoints | Developer Portal for YouTrack and Hub"
[3]: https://www.jetbrains.com/help/youtrack/devportal/authentication-with-permanent-token.html "Permanent Token Authorization | Developer Portal for YouTrack and ..."
[4]: https://www.jetbrains.com/help/youtrack/devportal/resource-api-issues.html "Issues | Developer Portal for YouTrack and Hub"
[5]: https://www.jetbrains.com/help/youtrack/devportal/api-query-syntax.html "Query Syntax | Developer Portal for YouTrack and Hub"
[6]: https://www.jetbrains.com/help/youtrack/devportal/api-howto-create-issue.html "Create an Issue | Developer Portal for YouTrack and Hub"
[7]: https://www.postman.com/lunar-module-geologist-27177224/ggwp/request/ahfzhcu/update-a-specific-issue "Update a Specific Issue | YouTrack REST API"
[8]: https://www.jetbrains.com/help/youtrack/devportal/resource-api-issues-issueID-links.html "Issue Links | Developer Portal for YouTrack and Hub"
[9]: https://www.jetbrains.com/help/youtrack/devportal/resource-api-issueLinkTypes.html "Issue Link Types | Developer Portal for YouTrack and Hub"
[10]: https://www.jetbrains.com/help/youtrack/devportal/resource-api-issues-issueID-comments.html "Issue Comments | Developer Portal for YouTrack and Hub"
[11]: https://www.jetbrains.com/help/youtrack/devportal/resource-api-issues-issueID-attachments.html "Issue Attachments | Developer Portal for YouTrack and Hub"
[12]: https://www.jetbrains.com/help/youtrack/devportal/api-fields-syntax.html "Fields Syntax | Developer Portal for YouTrack and Hub"
[13]: https://www.jetbrains.com/help/youtrack/devportal/api-concept-pagination.html "Pagination | Developer Portal for YouTrack and Hub"
[14]: https://www.postman.com/youtrack-dev/youtrack/documentation/sd7pq8x/youtrack-rest-api "YouTrack REST API | Documentation"