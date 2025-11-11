# Development Standards & Best Practices

## Core Development Principles

### SOLID Principles
- **Single Responsibility Principle**: Each module/class/function has one reason to change
- **Open/Closed Principle**: Software entities should be open for extension, closed for modification
- **Liskov Substitution Principle**: Objects should be replaceable with instances of their subtypes
- **Interface Segregation Principle**: Many specific interfaces are better than one general-purpose interface
- **Dependency Inversion Principle**: Depend on abstractions, not concretions

### DRY (Don't Repeat Yourself)
- **No code duplication**: Extract common functionality into shared modules
- **Configuration centralization**: Single source of truth for configuration values
- **Shared constants**: Define constants once, import everywhere needed
- **Utility functions**: Common operations in dedicated utility modules

### KISS (Keep It Simple, Stupid)
- **Simple solutions first**: Choose the simplest approach that works
- **Minimal dependencies**: Only add dependencies when absolutely necessary
- **Clear data flow**: Predictable input → processing → output patterns
- **Avoid over-engineering**: Build for current requirements, not imagined future needs

---

## Naming Conventions

### General Rules
- **Use descriptive, industry-standard names**
- **Avoid brand names, geographical references, or subjective descriptors**
- **Follow language-specific conventions** (snake_case for Rust, camelCase for TypeScript)
- **Be consistent across the entire codebase**

### ❌ Prohibited Terms
```
// Never use these terms in naming
- hybrid, universal, super, advanced, basic, simple
- production, staging, dev, local, test
- mexico, latam, us, regional, global
- custom, special, magic, smart, intelligent
- new, old, legacy, modern, next, improved
- manager, handler, processor, controller (unless truly accurate)
```

### ✅ Preferred Naming Patterns

**Functions/Methods:**
```rust
// ✅ Good - Describes what it does
fn create_session() -> Session {}
fn validate_token() -> Result<Claims, Error> {}
fn encode_audio(samples: &[f32]) -> EncodedAudio {}

// ❌ Bad - Vague or brand-specific
fn setup_session() -> Session {}
fn check_token() -> bool {}
fn process_audio() -> Audio {}
```

**Structs/Classes:**
```rust
// ✅ Good - Clear domain concepts
struct MediaSession {}
struct AudioCodec {}
struct ConnectionPool {}
struct RateLimiter {}

// ❌ Bad - Vague or non-standard
struct SessionManager {}
struct AudioProcessor {}
struct SmartConnection {}
struct AdvancedLimiter {}
```

**Variables:**
```rust
// ✅ Good - Specific and clear
let participant_count: u32;
let audio_bitrate: u32;
let connection_timeout: Duration;
let max_participants: u32;

// ❌ Bad - Ambiguous
let count: u32;
let quality: u32;
let timeout: Duration;
let limit: u32;
```

**Constants:**
```rust
// ✅ Good - Descriptive constants
const DEFAULT_AUDIO_SAMPLE_RATE: u32 = 48000;
const MAX_ROOM_PARTICIPANTS: u32 = 1000;
const ICE_CONNECTION_TIMEOUT: Duration = Duration::from_secs(30);

// ❌ Bad - Vague constants
const AUDIO_RATE: u32 = 48000;
const PARTICIPANT_LIMIT: u32 = 1000;
const TIMEOUT: Duration = Duration::from_secs(30);
```

**API Endpoints:**
```typescript
// ✅ Good - RESTful, resource-based
POST   /v1/rooms
GET    /v1/rooms/{roomId}
POST   /v1/rooms/{roomId}/participants
DELETE /v1/rooms/{roomId}/participants/{participantId}
GET    /v1/recordings
POST   /v1/recordings/{recordingId}/start

// ❌ Bad - Action-based or vague
POST   /v1/create-room
GET    /v1/get-room/{id}
POST   /v1/join
DELETE /v1/remove-user/{id}
GET    /v1/files
POST   /v1/start-recording
```

---

## API Design Standards

### RESTful Design
```typescript
// Resource-based URLs
GET    /v1/{resource}              // List resources
POST   /v1/{resource}              // Create resource
GET    /v1/{resource}/{id}         // Get specific resource
PUT    /v1/{resource}/{id}         // Update entire resource
PATCH  /v1/{resource}/{id}         // Partial update
DELETE /v1/{resource}/{id}         // Delete resource

// Sub-resources
GET    /v1/rooms/{roomId}/participants
POST   /v1/rooms/{roomId}/participants
DELETE /v1/rooms/{roomId}/participants/{participantId}
```

### Request/Response Format
```typescript
// Standard error format
interface ErrorResponse {
  error: {
    code: string;           // Machine-readable error code
    message: string;        // Human-readable message
    details?: any;          // Additional error context
    request_id: string;     // For debugging/support
  };
}

// Standard success format
interface SuccessResponse<T> {
  data: T;
  meta?: {
    pagination?: PaginationMeta;
    request_id: string;
  };
}

// Standard pagination
interface PaginationMeta {
  page: number;
  per_page: number;
  total: number;
  total_pages: number;
}
```

### Status Codes
```typescript
// Use standard HTTP status codes
200 // OK - Successful GET, PUT, PATCH
201 // Created - Successful POST
202 // Accepted - Async operation started
204 // No Content - Successful DELETE
400 // Bad Request - Invalid request data
401 // Unauthorized - Invalid/missing authentication
403 // Forbidden - Valid auth but insufficient permissions
404 // Not Found - Resource doesn't exist
409 // Conflict - Resource conflict (e.g., already exists)
422 // Unprocessable Entity - Valid JSON but invalid data
429 // Too Many Requests - Rate limit exceeded
500 // Internal Server Error - Server-side error
503 // Service Unavailable - Temporary service issue
```

### Parameter Validation
```rust
// Input validation with clear error messages
use serde::{Deserialize, Serialize};
use validator::{Validate, ValidationError};

#[derive(Debug, Deserialize, Validate)]
struct CreateRoomRequest {
    #[validate(length(min = 1, max = 100))]
    name: String,
    
    #[validate(range(min = 1, max = 1000))]
    max_participants: u32,
    
    #[validate(custom = "validate_duration")]
    duration_minutes: Option<u32>,
}

fn validate_duration(duration: &u32) -> Result<(), ValidationError> {
    if *duration > 0 && *duration <= 1440 { // Max 24 hours
        Ok(())
    } else {
        Err(ValidationError::new("invalid_duration"))
    }
}
```

---

## Code Structure Standards

### Module Organization
```
src/
├── api/                    # API layer
│   ├── handlers/          # Request handlers
│   ├── middleware/        # HTTP middleware
│   ├── routes/           # Route definitions
│   └── validators/       # Request validation
├── core/                  # Business logic
│   ├── audio/            # Audio processing
│   ├── media/            # Media management
│   ├── session/          # Session management
│   └── signaling/        # WebRTC signaling
├── infrastructure/       # External services
│   ├── database/         # Database access
│   ├── storage/          # File storage
│   ├── metrics/          # Monitoring
│   └── cache/            # Caching layer
├── types/                # Shared types/models
├── utils/                # Utility functions
└── config/               # Configuration
```

### Error Handling
```rust
// Define specific error types
#[derive(Debug, thiserror::Error)]
pub enum SessionError {
    #[error("Session not found: {session_id}")]
    NotFound { session_id: String },
    
    #[error("Session capacity exceeded: {current}/{max}")]
    CapacityExceeded { current: u32, max: u32 },
    
    #[error("Invalid session state: expected {expected}, got {actual}")]
    InvalidState { expected: String, actual: String },
    
    #[error("Database error: {0}")]
    Database(#[from] sqlx::Error),
}

// Result type aliases for consistency
pub type SessionResult<T> = Result<T, SessionError>;
pub type ApiResult<T> = Result<T, ApiError>;
```

### Function Signatures
```rust
// Clear, descriptive function signatures
pub async fn create_session(
    db: &DatabasePool,
    request: CreateSessionRequest,
) -> SessionResult<Session> {
    // Implementation
}

// Avoid boolean parameters - use enums instead
pub enum AudioCodec {
    Opus,
    G722,
    PCMU,
}

pub fn configure_audio_codec(codec: AudioCodec) -> AudioConfig {
    // Implementation
}

// Not: configure_audio(use_opus: bool, high_quality: bool)
```

---

## Documentation Standards

### Code Documentation
```rust
/// Creates a new WebRTC session with specified configuration.
///
/// # Arguments
/// * `config` - Session configuration including codec preferences and limits
/// * `participant_id` - Unique identifier for the initial participant
///
/// # Returns
/// Returns a `Session` instance on success, or `SessionError` if:
/// - Configuration is invalid
/// - Database connection fails
/// - Maximum sessions limit reached
///
/// # Example
/// ```rust
/// let config = SessionConfig::default();
/// let session = create_session(config, "user123").await?;
/// ```
pub async fn create_session(
    config: SessionConfig,
    participant_id: &str,
) -> SessionResult<Session> {
    // Implementation
}
```

### API Documentation
```yaml
# OpenAPI 3.0 specification for all APIs
paths:
  /v1/rooms:
    post:
      summary: Create a new room
      description: |
        Creates a new room for media sessions. The room will be automatically
        deleted after the specified duration or when the last participant leaves.
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CreateRoomRequest'
            examples:
              basic:
                summary: Basic room creation
                value:
                  name: "Team Meeting"
                  max_participants: 10
      responses:
        '201':
          description: Room created successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Room'
```

---

## Testing Standards

### Test Organization
```rust
#[cfg(test)]
mod tests {
    use super::*;
    use crate::test_utils::*;

    // Test naming: test_{function_name}_{scenario}_{expected_outcome}
    #[tokio::test]
    async fn test_create_session_valid_request_returns_session() {
        // Arrange
        let db = create_test_database().await;
        let config = SessionConfig::default();
        
        // Act
        let result = create_session(&db, config, "user123").await;
        
        // Assert
        assert!(result.is_ok());
        let session = result.unwrap();
        assert_eq!(session.participant_count(), 1);
    }

    #[tokio::test]
    async fn test_create_session_invalid_config_returns_validation_error() {
        // Arrange
        let db = create_test_database().await;
        let config = SessionConfig {
            max_participants: 0, // Invalid
            ..Default::default()
        };
        
        // Act
        let result = create_session(&db, config, "user123").await;
        
        // Assert
        assert!(matches!(result, Err(SessionError::InvalidConfig { .. })));
    }
}
```

### Integration Tests
```rust
// Integration tests in tests/ directory
// tests/api_integration.rs
use serde_json::json;

#[tokio::test]
async fn test_room_creation_workflow() {
    let app = create_test_app().await;
    
    // Create room
    let response = app
        .post("/v1/rooms")
        .json(&json!({
            "name": "Test Room",
            "max_participants": 5
        }))
        .send()
        .await;
    
    assert_eq!(response.status(), 201);
    let room: Room = response.json().await;
    
    // Verify room exists
    let response = app
        .get(&format!("/v1/rooms/{}", room.id))
        .send()
        .await;
    
    assert_eq!(response.status(), 200);
}
```

---

## Performance Standards

### Async/Await Best Practices
```rust
// Use async/await properly
pub async fn process_multiple_streams(
    streams: Vec<StreamId>,
) -> Result<Vec<ProcessedStream>, ProcessingError> {
    // Process streams concurrently
    let futures = streams.into_iter()
        .map(|stream_id| process_single_stream(stream_id));
    
    // Wait for all to complete, collect results
    let results = futures::future::try_join_all(futures).await?;
    Ok(results)
}

// Avoid blocking operations in async context
pub async fn save_recording(data: &[u8]) -> Result<RecordingId, StorageError> {
    // ✅ Good - Use async file operations
    tokio::fs::write("recording.wav", data).await?;
    
    // ❌ Bad - Blocking operation in async context
    // std::fs::write("recording.wav", data)?;
    
    Ok(RecordingId::new())
}
```

### Memory Management
```rust
// Use appropriate data structures
use std::collections::HashMap;
use dashmap::DashMap; // Concurrent HashMap

// For concurrent access
pub struct SessionManager {
    sessions: DashMap<SessionId, Session>,
}

// Pre-allocate when size is known
pub fn process_audio_batch(samples: &[f32]) -> Vec<f32> {
    let mut processed = Vec::with_capacity(samples.len());
    // Process samples...
    processed
}

// Use references to avoid unnecessary clones
pub fn validate_session_config(config: &SessionConfig) -> ValidationResult {
    // Work with reference, don't take ownership
}
```

---

## Security Best Practices

### Input Validation
```rust
use validator::Validate;

#[derive(Validate)]
pub struct CreateRoomRequest {
    #[validate(length(min = 1, max = 100))]
    #[validate(regex = "^[a-zA-Z0-9 ._-]+$")]
    name: String,
    
    #[validate(range(min = 1, max = 1000))]
    max_participants: u32,
    
    #[validate(custom = "validate_room_type")]
    room_type: RoomType,
}

// Sanitize all inputs
pub fn sanitize_room_name(name: &str) -> String {
    name.chars()
        .filter(|c| c.is_alphanumeric() || " ._-".contains(*c))
        .take(100)
        .collect()
}
```

### Authentication & Authorization
```rust
// Clear permission checking
#[derive(Debug, Clone)]
pub enum Permission {
    CreateRoom,
    JoinRoom,
    ModerateRoom,
    AccessRecordings,
}

pub async fn check_permission(
    user_id: &str,
    permission: Permission,
    resource_id: Option<&str>,
) -> Result<bool, AuthError> {
    // Implementation
}

// Use in handlers
pub async fn create_room_handler(
    user: AuthenticatedUser,
    request: CreateRoomRequest,
) -> ApiResult<Room> {
    check_permission(&user.id, Permission::CreateRoom, None).await?;
    // Create room...
}
```

---

## Configuration Management

### Environment-based Configuration
```rust
use serde::{Deserialize, Serialize};

#[derive(Debug, Deserialize)]
pub struct DatabaseConfig {
    pub url: String,
    pub max_connections: u32,
    pub connection_timeout_seconds: u64,
}

#[derive(Debug, Deserialize)]
pub struct ServerConfig {
    pub host: String,
    pub port: u16,
    pub tls_cert_path: Option<String>,
    pub tls_key_path: Option<String>,
}

#[derive(Debug, Deserialize)]
pub struct Config {
    pub database: DatabaseConfig,
    pub server: ServerConfig,
    pub media: MediaConfig,
    pub auth: AuthConfig,
}

// Load from environment
impl Config {
    pub fn from_env() -> Result<Self, ConfigError> {
        envy::from_env().map_err(ConfigError::Parse)
    }
}
```

### Feature Flags
```rust
#[derive(Debug, Clone)]
pub struct FeatureFlags {
    pub enable_recording: bool,
    pub enable_transcription: bool,
    pub max_session_duration_minutes: u32,
    pub enable_simulcast: bool,
}

impl Default for FeatureFlags {
    fn default() -> Self {
        Self {
            enable_recording: true,
            enable_transcription: false,
            max_session_duration_minutes: 480, // 8 hours
            enable_simulcast: true,
        }
    }
}
```

---

## Monitoring & Observability

### Structured Logging
```rust
use tracing::{info, warn, error, debug};

#[tracing::instrument(skip(db))]
pub async fn create_session(
    db: &DatabasePool,
    config: SessionConfig,
    participant_id: &str,
) -> SessionResult<Session> {
    info!(
        participant_id = %participant_id,
        max_participants = config.max_participants,
        "Creating new session"
    );
    
    let session = Session::create(config).await?;
    
    info!(
        session_id = %session.id,
        participant_id = %participant_id,
        "Session created successfully"
    );
    
    Ok(session)
}
```

### Metrics Collection
```rust
use metrics::{counter, histogram, gauge};

pub async fn handle_session_creation() -> Result<Session, Error> {
    let start_time = std::time::Instant::now();
    
    // Business logic
    let result = create_session().await;
    
    // Record metrics
    histogram!("session_creation_duration_ms", start_time.elapsed().as_millis() as f64);
    
    match &result {
        Ok(_) => {
            counter!("sessions_created_total").increment(1);
            gauge!("active_sessions").increment(1.0);
        }
        Err(_) => {
            counter!("session_creation_errors_total").increment(1);
        }
    }
    
    result
}
```

---

## Developer Experience (DX) Standards

### SDK Design Principles
```typescript
// Principle: Make simple things simple, complex things possible

// ✅ Simple case - minimal code required
const session = await MediaSession.create();
await session.enableMicrophone();
await session.join("room-123");

// ✅ Complex case - full control available
const session = await MediaSession.create({
  audio: {
    codec: AudioCodec.Opus,
    sampleRate: 48000,
    echoCancellation: true,
    noiseSuppression: 'aggressive'
  },
  video: {
    codec: VideoCodec.VP9,
    resolution: { width: 1920, height: 1080 },
    framerate: 30
  },
  network: {
    turnServers: [...],
    iceTransportPolicy: 'relay'
  }
});
```

### Error Messages
```typescript
// ✅ Helpful error messages with solutions
interface ApiError {
  code: string;
  message: string;
  details?: {
    field?: string;
    suggestion?: string;
    documentation_url?: string;
  };
}

// Example error response
{
  "error": {
    "code": "invalid_audio_codec",
    "message": "The specified audio codec 'MP3' is not supported",
    "details": {
      "field": "audio.codec",
      "suggestion": "Use 'opus', 'g722', or 'pcmu'",
      "documentation_url": "https://docs.example.com/audio-codecs"
    }
  }
}
```

### TypeScript Types
```typescript
// Export comprehensive types for excellent IDE support
export interface MediaSession {
  readonly id: string;
  readonly state: SessionState;
  readonly participants: ReadonlyArray<Participant>;
  readonly localStreams: ReadonlyArray<MediaStream>;
  
  // Methods with clear return types
  enableMicrophone(deviceId?: string): Promise<MediaStreamTrack>;
  enableCamera(deviceId?: string): Promise<MediaStreamTrack>;
  publishStream(stream: MediaStream): Promise<PublishedStream>;
  
  // Event listeners with typed events
  on<T extends keyof SessionEvents>(
    event: T, 
    listener: (data: SessionEvents[T]) => void
  ): void;
}

// Comprehensive event types
export interface SessionEvents {
  'participant-joined': { participant: Participant; timestamp: Date };
  'participant-left': { participant: Participant; reason: string };
  'stream-added': { stream: RemoteStream; participant: Participant };
  'connection-state-changed': { 
    previousState: ConnectionState; 
    currentState: ConnectionState 
  };
}
```

---

## Code Review Checklist

### Before Submitting PR
- [ ] **Naming follows conventions** - No prohibited terms, descriptive names
- [ ] **Functions are single-purpose** - Each function does one thing well
- [ ] **Error handling is comprehensive** - All failure cases handled
- [ ] **Tests are included** - Unit tests for logic, integration tests for APIs
- [ ] **Documentation is updated** - API docs, code comments, README if needed
- [ ] **Performance is considered** - No obvious bottlenecks introduced
- [ ] **Security is validated** - Input validation, no secrets exposed
- [ ] **Types are exported** - TypeScript definitions for public APIs

### Code Quality Gates
- **Compile without warnings** - Zero compilation warnings allowed
- **Pass all tests** - 100% test pass rate required
- **Meet coverage threshold** - Minimum 80% code coverage
- **Pass security scan** - No high/critical vulnerabilities
- **Performance regression check** - No significant performance degradation
- **API compatibility check** - No breaking changes without version bump

---

This document serves as the foundation for maintaining high-quality, developer-friendly code throughout the project. All team members should refer to these standards during development and code review processes.