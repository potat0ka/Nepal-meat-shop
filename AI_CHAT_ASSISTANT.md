# 🤖 AI Chat Assistant - Nepal Meat Shop

## Overview
The Nepal Meat Shop now includes an AI-powered chat assistant that can communicate with customers in multiple languages and help them with their inquiries about products, orders, and general shop information.

## Features

### 🌐 Multilingual Support
- **English**: Standard English communication
- **Nepali (Devanagari)**: नेपाली भाषामा सञ्चार
- **Nepali (Romanized)**: Nepali written in English letters

### 🧠 AI Capabilities
- Product information and availability
- Pricing inquiries
- Delivery information
- Order assistance
- General customer support
- Polite conversation handling

## API Endpoints

### POST `/api/chat`
Send a message to the AI assistant.

**Request Body:**
```json
{
  "message": "Your message here"
}
```

**Response:**
```json
{
  "reply": "AI assistant response",
  "language_detected": "english|nepali_romanized|nepali_devanagari",
  "response_time_ms": 500
}
```

### GET `/api/chat/history`
Get chat history for authenticated users.

**Query Parameters:**
- `page`: Page number (default: 1)
- `per_page`: Items per page (default: 20, max: 100)

**Response:**
```json
{
  "chats": [
    {
      "user_message": "Hello",
      "bot_reply": "Hi there!",
      "timestamp": "2025-01-16T10:30:00",
      "language_detected": "english"
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 50,
    "pages": 3
  }
}
```

### GET `/api/chat/stats`
Get chat statistics (admin only).

**Response:**
```json
{
  "total_chats": 1000,
  "language_distribution": [
    {"_id": "english", "count": 600},
    {"_id": "nepali_romanized", "count": 300},
    {"_id": "nepali_devanagari", "count": 100}
  ],
  "average_response_time_ms": 450.5
}
```

## Setup Instructions

### 1. Install Dependencies
```bash
pip install openai>=1.99.0
```

### 2. Configure OpenAI API Key
Add your OpenAI API key to the `.env.mongo` file:
```env
OPENAI_API_KEY=your_openai_api_key_here
```

**Get your API key from:** https://platform.openai.com/api-keys

### 3. MongoDB Collection
The chat history is automatically stored in the `chats` collection with the following schema:
```javascript
{
  user_message: String,      // Required
  bot_reply: String,         // Required
  timestamp: Date,           // Required, auto-generated
  user_id: ObjectId,         // Optional, if user is logged in
  session_id: String,        // Optional, for grouping conversations
  language_detected: String, // Auto-detected language
  response_time_ms: Number   // Performance tracking
}
```

## Usage Examples

### English
```bash
curl -X POST http://127.0.0.1:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What types of meat do you sell?"}'
```

### Romanized Nepali
```bash
curl -X POST http://127.0.0.1:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Namaste, tapai ko pasal ma kasto masu cha?"}'
```

### Devanagari Nepali
```bash
curl -X POST http://127.0.0.1:5000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "नमस्ते, तपाईंको पसलमा कस्तो मासु छ?"}'
```

## Language Detection

The system automatically detects the language based on:
- **Devanagari Script**: Presence of Unicode characters in range U+0900-U+097F
- **Romanized Nepali**: Common Nepali words written in English letters
- **English**: Default fallback language

## Error Handling

- **Missing OpenAI API Key**: Returns 503 Service Unavailable
- **OpenAI API Errors**: Returns appropriate fallback messages in detected language
- **Database Errors**: Logged but don't prevent chat functionality
- **Invalid Requests**: Returns 400 Bad Request with error details

## Performance

- **Model Used**: GPT-4o-mini (cost-effective and fast)
- **Average Response Time**: ~500ms
- **Max Tokens**: 500 per response
- **Temperature**: 0.7 (balanced creativity)

## Security

- Chat history is linked to user accounts when authenticated
- Admin-only access to chat statistics
- API key stored securely in environment variables
- Input validation and sanitization

## Integration Notes

- **Non-intrusive**: Added without modifying existing code
- **Modular Design**: Easy to extend or modify
- **Database Agnostic**: Uses existing MongoDB connection
- **Blueprint Architecture**: Follows Flask best practices

---

**Note**: To use the AI features, you must have a valid OpenAI API key. The system will work without it but will return fallback messages instead of AI-generated responses.