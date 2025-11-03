# Backend Improvement TODO List

This file outlines potential improvements for the EchoNote backend application.

## 1. Code Structure & Refactoring

- [ ] **Refactor CRUD operations into a repository pattern.**
  - Create a `backend/crud.py` or `backend/repository.py` file.
  - Move database logic from `main.py` into functions in the new file (e.g., `create_transcription`, `get_transcription_by_id`, `list_transcriptions`, `delete_transcription`).
  - This will make the API endpoints in `main.py` cleaner and more focused on handling HTTP requests and responses.

- [ ] **Add a conversion method to the `Transcription` model.**
  - Create a method on the `Transcription` model in `models.py` to convert it to a `TranscriptionPublic` object.
  - This will reduce code duplication in `main.py`.

## 2. Features

- [ ] **Calculate and store audio duration.**
  - In the `transcribe_audio` endpoint in `main.py`, use a library like `soundfile` or `pydub` to get the duration of the uploaded audio file.
  - Store the duration in the `duration_seconds` field of the `Transcription` model.

- [ ] **Implement basic API key authentication.**
  - Add a new setting for an API key in `config.py`.
  - Create a dependency in `main.py` that checks for a valid API key in the request headers (e.g., `X-API-Key`).
  - Protect the CRUD endpoints with this dependency.

## 3. Error Handling & Validation

- [ ] **Improve error handling in `transcribe_audio`.**
  - Add more specific `try...except` blocks to handle potential errors from the transcription service (e.g., connection errors, API errors) and database errors separately from generic exceptions.

- [ ] **Add validation for pagination parameters.**
  - In the `list_transcriptions` endpoint, add validation to ensure that `skip` and `limit` are non-negative integers.

## 4. Testing

- [ ] **Set up a testing framework (e.g., `pytest`).**
  - Add `pytest` and `httpx` to `requirements.txt`.
  - Create a `tests` directory in the `backend` folder.
  - Configure `pytest` with a separate test database.

- [ ] **Write unit tests for the repository/CRUD functions.**
  - Create `tests/test_crud.py`.
  - Write tests for creating, reading, updating, and deleting transcriptions.

- [ ] **Write integration tests for the API endpoints.**
  - Create `tests/test_api.py`.
  - Write tests for the `/api/transcribe` and `/api/transcriptions` endpoints, mocking the transcription service where necessary.

## 5. Database

- [ ] **Optimize the total count query in `list_transcriptions`.**
  - Instead of fetching all transcriptions to get the count, use `session.exec(select(func.count(Transcription.id))).one()` for a more efficient query.

## 6. Dependency Management

- [ ] **Use `pip-tools` to manage dependencies.**
  - Create a `requirements.in` file with the top-level dependencies.
  - Use `pip-compile` to generate a pinned `requirements.txt` file.
  - This will make the dependency management more robust and reproducible.
