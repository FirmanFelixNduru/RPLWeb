Build a simple full-stack web application named **Lecturer GitHub Tracker**.

Purpose:
Help lecturers monitor GitHub repository activity for each student. The application collects commit data from student GitHub repositories only when the lecturer presses a button, stores it in MySQL, and shows the progress summary on a dashboard.

Use this stack:

* Frontend: React + TypeScript + Vite + Tailwind CSS
* Backend: Node.js + TypeScript + Express
* Database: MySQL
* ORM: Prisma
* API style: REST API
* GitHub integration: GitHub REST API
* Use Docker Compose for MySQL
* Use `.env.example` for database URL and optional GitHub token

Code rules:

* Do not add comments unless truly necessary.
* Use PascalCase for all classes, types, interfaces, enums, React components, database models, API DTOs, and JSON property names.
* Local variables may use camelCase.
* Keep code lines below 150 characters where practical.
* Use a clean and simple folder structure.
* Do not add authentication in this first version. Assume one lecturer uses the application.

Main entities:

1. Course

   * Id
   * Name
   * Semester
   * Year
   * CreatedAt

2. Student

   * Id
   * CourseId
   * StudentNumber
   * Name
   * Email
   * GithubUsername
   * CreatedAt

3. Repository

   * Id
   * StudentId
   * Name
   * RepositoryUrl
   * Owner
   * RepositoryName
   * IsActive
   * LastSyncedAt
   * CreatedAt

4. Commit

   * Id
   * RepositoryId
   * Sha
   * Message
   * AuthorName
   * AuthorEmail
   * CommittedAt
   * CommitUrl
   * CreatedAt

Database rules:

* A Commit must be unique by `RepositoryId` and `Sha`.
* Never delete existing commit data during synchronization.
* Never replace existing commit records.
* When data is fetched again, save only commits that do not already exist in the database.
* Update `LastSyncedAt` after a successful synchronization.
* Use Prisma migrations and seed one example course, three students, and public GitHub repositories.

Backend features:

1. CRUD Course

   * Create, list, detail, update, delete course.

2. CRUD Student

   * Create, list, detail, update, delete student inside a course.

3. CRUD Repository

   * Add, edit, delete repository for a student.
   * Validate and parse GitHub repository URL such as `https://github.com/owner/repository`.

4. Manual GitHub Commit Synchronization

   * Endpoint to synchronize one repository.
   * Endpoint to synchronize all active repositories in a course.
   * Synchronization is started only by a button click from the frontend.
   * Read commits from the GitHub API.
   * Insert only new commits using `RepositoryId` and `Sha`.
   * Do not delete or overwrite any existing commit.
   * Return a result containing:

     * RepositoryId
     * FetchedCommitCount
     * NewCommitCount
     * ExistingCommitCount
     * LastSyncedAt
     * Message
   * Handle public repositories first.
   * If `GITHUB_TOKEN` is available, use it as a Bearer token for GitHub API requests.
   * Show a meaningful error if a repository is private, invalid, unavailable, or GitHub API rate limit is reached.

5. Dashboard API

   * Return a course summary:

     * TotalStudents
     * TotalRepositories
     * TotalCommits
     * ActiveStudents
     * InactiveStudents
     * StudentsWithoutCommits
   * Return student progress data:

     * StudentId
     * StudentName
     * StudentNumber
     * RepositoryCount
     * TotalCommits
     * LatestCommitAt
     * ActivityStatus
   * ActivityStatus rules:

     * `NO_COMMIT`: no commit stored
     * `INACTIVE`: last commit is older than 14 days
     * `ACTIVE`: last commit is within 14 days

Frontend pages:

1. Dashboard

   * Course selector.
   * Summary cards: total students, repositories, commits, active students, and students without commits.
   * Table showing each student, repository count, total commits, latest commit date, and activity status.
   * Button: `Sync All Repositories`.
   * Show loading state, successful sync message, and error message.
   * Dashboard reads only from the MySQL database when opened. It must not call GitHub automatically.

2. Course Management

   * List courses.
   * Form to create and edit courses.
   * Button to open course dashboard.

3. Student Management

   * List students in a selected course.
   * Form to add and edit student information.
   * Show student GitHub username.

4. Repository Management

   * List repositories for a selected student.
   * Form to add and edit GitHub repository URLs.
   * Button: `Sync Commits`.
   * Show last sync time and number of stored commits.

5. Student Progress Detail

   * Show student information.
   * Show repositories.
   * Show total commits and latest commit.
   * Show commit history table with commit message, author, date, SHA, and link to GitHub commit.

UI requirements:

* Use Indonesian language for all labels, buttons, messages, and validation.
* Create a clean, responsive lecturer dashboard.
* Use simple tables, cards, badges, forms, confirmation dialog before delete, and empty states.
* Use status badge colors:

  * Active: green
  * Inactive: orange
  * No Commit: red
* Do not add charts in the first version.

Required API routes:

* `GET /api/courses`
* `POST /api/courses`
* `GET /api/courses/:Id`
* `PUT /api/courses/:Id`
* `DELETE /api/courses/:Id`
* `GET /api/courses/:CourseId/students`
* `POST /api/courses/:CourseId/students`
* `PUT /api/students/:Id`
* `DELETE /api/students/:Id`
* `GET /api/students/:Id/repositories`
* `POST /api/students/:Id/repositories`
* `PUT /api/repositories/:Id`
* `DELETE /api/repositories/:Id`
* `POST /api/repositories/:Id/sync`
* `POST /api/courses/:CourseId/sync`
* `GET /api/courses/:CourseId/dashboard`
* `GET /api/students/:Id/progress`

Deliverables:

* Complete frontend and backend source code.
* Prisma schema, migration, and seed data.
* Docker Compose file for MySQL.
* `.env.example`.
* README with installation, database migration, seed, frontend/backend startup, Docker usage, and GitHub token configuration.
* Ensure the application builds successfully and all basic CRUD plus manual commit synchronization work.


Project structure:

* Use a TypeScript monorepo with npm workspaces.
* Structure:

```text
lecturer-github-tracker/
  apps/
    web/
    api/
  packages/
    shared/
```

Shared package requirements:

* Create `packages/shared` as `@lecturer-github-tracker/shared`.
* Store all shared domain models, enums, API response types, and shared constants here.
* Both `apps/web` and `apps/api` must import shared types from this package.
* Do not duplicate domain model definitions between frontend and backend.

Example shared files:

```text
packages/shared/src/
  models/
    User.ts
    Course.ts
    Student.ts
    Repository.ts
    Commit.ts
  enums/
    ActivityStatus.ts
  dto/
    DashboardResponse.ts
    SyncResult.ts
  index.ts
```

Model rules:

* Define shared TypeScript interfaces or types only once in `packages/shared`.
* Example: `Student`, `Repository`, `Commit`, and `ActivityStatus` must be imported by both frontend and backend from `@lecturer-github-tracker/shared`.
* Prisma models remain in the backend because they are database-specific.
* The backend maps Prisma entities to shared API models before returning responses.
* The frontend must not import Prisma types.
* Configure TypeScript paths, workspace dependencies, build scripts, and development scripts correctly so all packages compile successfully.
