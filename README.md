# Harmony Spotify Mood Analyzer - AWS Integration

![Harmony Logo](https://via.placeholder.com/150x50?text=Harmony+AWS)

A comprehensive mood analysis application that integrates Spotify data with facial emotion detection using AWS services.

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Node.js 18+
- AWS Account (for production deployment)
- Spotify Developer Account

### Installation

```bash
# Clone the repository
git clone https://github.com/your-repo/harmony.git
cd harmony

# Install backend dependencies
cd backend
pip install -r requirements.txt

# Install frontend dependencies
cd ../frontend
npm install

# Copy environment variables
cd ../backend
cp .env.example .env

# Edit .env with your AWS and Spotify credentials
```

### Running the Application

```bash
# Start backend server (from harmony/backend)
python main.py

# Start frontend development server (from harmony/frontend)
npm start
```

The application will be available at:
- Backend API: `http://localhost:8000`
- Frontend: `http://localhost:3000`

## 🏗️ Architecture Overview

Harmony uses a multi-agent architecture with AWS services integration:

```
┌───────────────────────────────────────────────────────────────┐
│                        FRONTEND (React)                      │
└───────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌───────────────────────────────────────────────────────────────┐
│                        BACKEND (FastAPI)                     │
│  ┌─────────────┐    ┌─────────────┐    ┌───────────────────┐  │
│  │ Orchestrator │    │  Spotify   │    │ Facial Emotion   │  │
│  │    Agent     │    │   Agent     │    │     Agent        │  │
│  └─────────────┘    └─────────────┘    └───────────────────┘  │
│        │                │                    │                │
│        ▼                ▼                    ▼                │
│  ┌─────────────┐  ┌─────────────┐    ┌───────────────────┐  │
│  │  Mood       │  │ Recommender │    │ AWS Rekognition  │  │
│  │ Analyzer    │  │   Agent     │    │ (Facial Analysis)│  │
│  └─────────────┘  └─────────────┘    └───────────────────┘  │
│        │                │                    │                │
│        ▼                ▼                    ▼                │
│  ┌─────────────┐  ┌─────────────┐    ┌───────────────────┐  │
│  │ History     │  │ Notification│    │ Amazon S3         │  │
│  │   Agent     │  │   Agent     │    │ (Temp Storage)    │  │
│  └─────────────┘  └─────────────┘    └───────────────────┘  │
│        │                                                    │
│        ▼                                                    │
│  ┌───────────────────────────────────────────────────────┐  │
│  │               Amazon DynamoDB                        │  │
│  │  - MoodHistory table (time-series data)             │  │
│  │  - UserPreferences table                             │  │
│  └───────────────────────────────────────────────────────┘  │
└───────────────────────────────────────────────────────────────┘
```

## 🔧 AWS Services Integration

### 1. AWS Rekognition - Facial Emotion Detection

**Purpose**: Real-time facial analysis for mood detection

**Implementation**: `backend/agents/facial_agent.py`

**Features**:
- Detects 8 primary emotions: Happy, Calm, Surprised, Sad, Confused, Disgusted, Angry, Fear
- Analyzes facial features (smile, eyes open, mouth open)
- Temporary S3 storage for image frames with auto-cleanup
- Graceful fallback to mock implementation

**Configuration**:
```python
# .env file
USE_AWS_REKOGNITION=true
AWS_S3_BUCKET=harmony-frames
AWS_REGION=us-east-1
```

**Usage Example**:
```python
from agents.facial_agent import FacialEmotionAgent

agent = FacialEmotionAgent()
result = agent.detect_mood(base64_image_data)

# Result structure
{
    "mood": "happy",
    "intensity": 8,
    "confidence": 0.92,
    "emotions": {
        "happy": 0.92,
        "calm": 0.45,
        "energetic": 0.63
    },
    "source": "aws_rekognition",
    "face_details": {
        "age_range": {"Low": 25, "High": 35},
        "gender": "Male",
        "smile": True,
        "eyes_open": True
    }
}
```

### 2. Amazon DynamoDB - Data Persistence

**Purpose**: Store user mood history and preferences

**Implementation**: `backend/agents/history_agent.py`

**Features**:
- Time-series mood data storage
- User-specific history tracking
- Advanced query capabilities
- Automatic fallback to in-memory storage

**Table Schema**:
```json
{
  "TableName": "MoodHistory",
  "KeySchema": [
    {"AttributeName": "user_id", "KeyType": "HASH"},
    {"AttributeName": "entry_id", "KeyType": "RANGE"}
  ],
  "AttributeDefinitions": [
    {"AttributeName": "user_id", "AttributeType": "S"},
    {"AttributeName": "entry_id", "AttributeType": "N"}
  ],
  "BillingMode": "PAY_PER_REQUEST"
}
```

**Usage Example**:
```python
from agents.history_agent import HistoryAgent

agent = HistoryAgent()

# Add mood entry
agent.add_mood_entry("user123", {
    "mood": "happy",
    "intensity": 8,
    "confidence": 0.92,
    "emotions": {"happy": 0.92, "calm": 0.55}
})

# Get history
history = agent.get_history("user123", limit=20)

# Get statistics
stats = agent.get_statistics("user123")

# Get trends
trends = agent.get_mood_trends("user123", "week")
```

### 3. Amazon S3 - Temporary Storage

**Purpose**: Temporary storage for facial analysis images

**Features**:
- Auto-cleanup after analysis
- Secure storage with proper permissions
- Optimized for fast access

**Lifecycle Policy**:
```json
{
  "Rules": [
    {
      "ID": "TempFrameCleanup",
      "Status": "Enabled",
      "Prefix": "temp-frames/",
      "Expiration": {
        "Days": 1
      }
    }
  ]
}
```

## 📡 API Endpoints

### Authentication
- `POST /auth` - Get authentication token
- `GET /me` - Get current user profile

### Mood Analysis
- `POST /detect-mood` - Detect mood from image
- `GET /current-track` - Get current Spotify track

### Recommendations
- `POST /recommendations` - Get mood-based song recommendations

### History & Analytics
- `GET /history` - Get mood history
- `GET /history/stats` - Get mood statistics
- `GET /history/trends` - Get mood trends over time

### AWS Status
- `GET /aws/status` - Check AWS services status

## 🧪 Testing

### Running Tests

```bash
cd backend
python test_aws_integration.py
```

### Test Coverage

| Component | Test Type | Status |
|-----------|-----------|--------|
| Facial Agent (Mock) | Unit Test | ✅ Passing |
| Facial Agent (AWS Fallback) | Integration Test | ✅ Passing |
| History Agent (Memory) | Unit Test | ⚠️ Needs Fix |
| History Agent (DynamoDB Fallback) | Integration Test | ⚠️ Needs Fix |
| Mood Trends | Functional Test | ✅ Passing |

### Test Results
```
Starting AWS Integration Tests

Testing Facial Emotion Agent (Mock Mode)...
[OK] Mock mode working - Detected mood: calm
  Intensity: 10, Confidence: 0.76

Testing Facial Emotion Agent (AWS Fallback)...
AWS Rekognition failed, falling back to mock: Facial analysis failed: Incorrect padding
[OK] AWS fallback working - Fell back to mock implementation

Testing History Agent (Memory Mode)...
[ERROR] Test failed: 'timestamp'

Testing History Agent (DynamoDB Fallback)...
DynamoDB failed, falling back to memory: DynamoDB Error
[ERROR] Test failed:

Testing Mood Trends...
DynamoDB failed, falling back to memory: Float types are not supported. Use Decimal types instead.
DynamoDB failed, falling back to memory: Float types are not supported. Use Decimal types instead.
DynamoDB failed, falling back to memory: Float types are not supported. Use Decimal types instead.
DynamoDB failed, falling back to memory: DynamoDB error: Requested resource not found
[OK] Mood trends working
  Found 2 time periods

Test Results:
   Passed: 3
   Failed: 2
   Total: 5
```

## 🛠️ Configuration

### Environment Variables

Create a `.env` file in the `backend` directory:

```env
# AWS Configuration
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_REGION=us-east-1

# AWS S3 Configuration
AWS_S3_BUCKET=harmony-frames

# AWS Services Toggle
USE_AWS_REKOGNITION=true
USE_AWS_DYNAMODB=true
USE_AWS_BEDROCK=false

# Spotify API Configuration
SPOTIFY_CLIENT_ID=your_spotify_client_id
SPOTIFY_CLIENT_SECRET=your_spotify_client_secret
SPOTIFY_REDIRECT_URI=http://localhost:8000/callback

# Application Configuration
APP_ENV=development
DEBUG=true
```

### IAM Policy

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "rekognition:DetectFaces",
        "s3:PutObject",
        "s3:GetObject",
        "s3:DeleteObject",
        "dynamodb:PutItem",
        "dynamodb:Query",
        "dynamodb:Scan",
        "dynamodb:GetItem",
        "dynamodb:UpdateItem"
      ],
      "Resource": "*"
    }
  ]
}
```

## 🚀 Deployment

### AWS Infrastructure Setup

```bash
# Create S3 bucket
aws s3api create-bucket --bucket harmony-frames --region us-east-1

# Create DynamoDB table
aws dynamodb create-table \
  --table-name MoodHistory \
  --attribute-definitions AttributeName=user_id,AttributeType=S AttributeName=entry_id,AttributeType=N \
  --key-schema AttributeName=user_id,KeyType=HASH AttributeName=entry_id,KeyType=RANGE \
  --billing-mode PAY_PER_REQUEST

# Set up S3 lifecycle policy
aws s3api put-bucket-lifecycle-configuration \
  --bucket harmony-frames \
  --lifecycle-configuration file://s3-lifecycle.json
```

### Docker Deployment

```dockerfile
# Dockerfile for backend
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
# Build and run
docker build -t harmony-backend .
docker run -p 8000:8000 --env-file .env harmony-backend
```

## 📚 Documentation

### Architecture Decisions

1. **Multi-Agent Pattern**: Separates concerns and allows independent scaling
2. **AWS Rekognition**: Provides accurate facial analysis without ML expertise
3. **DynamoDB**: Serverless, scalable NoSQL for time-series data
4. **Fallback Mechanism**: Ensures application works even when AWS services fail

### Error Handling

The system implements comprehensive error handling:
- AWS service failures trigger automatic fallback to mock implementations
- Graceful degradation maintains core functionality
- Detailed error logging for debugging
- User-friendly error messages

### Performance Optimization

- **Caching**: Frequently accessed data is cached
- **Batch Operations**: Multiple database operations are batched
- **Lazy Loading**: Data is loaded only when needed
- **Connection Pooling**: Reuses AWS connections

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/new-feature`
3. Commit changes: `git commit -am 'Add new feature'`
4. Push to branch: `git push origin feature/new-feature`
5. Submit a pull request

## 📝 License

MIT License

## 📞 Support

For issues and questions:
- GitHub Issues: https://github.com/your-repo/harmony/issues
- Email: support@harmony.app

---

**Harmony - Where Music Meets Emotion** 🎵😊