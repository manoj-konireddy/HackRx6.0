# OpenRouter Setup Guide

This guide explains how to configure the Intelligent Query Retrieval System to use DeepSeek via OpenRouter.

## Why OpenRouter?

OpenRouter provides access to various AI models including DeepSeek, often at lower costs or with free tiers. The `deepseek/deepseek-r1-0528:free` model provides excellent performance for document analysis and query processing.

## Setup Steps

### 1. Get OpenRouter API Key

1. Visit [OpenRouter.ai](https://openrouter.ai/)
2. Sign up for an account
3. Navigate to the API Keys section
4. Generate a new API key
5. Copy the API key (starts with `sk-or-...`)

### 2. Configure Environment

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and set your OpenRouter API key:
   ```env
   # OpenRouter/DeepSeek Configuration
   OPENAI_API_KEY=sk-or-your-openrouter-api-key-here
   OPENAI_MODEL=deepseek/deepseek-r1-0528:free
   OPENAI_BASE_URL=https://openrouter.ai/api/v1
   
   # Other configurations...
   DATABASE_URL=postgresql://username:password@localhost:5432/intelligent_query_db
   ```

### 3. Test the Connection

Run the test script to verify your setup:

```bash
python test_openrouter.py
```

Expected output:
```
🧪 Testing OpenRouter/DeepSeek Integration
==================================================
✅ API Key found: sk-or-12...
🔄 Testing basic chat completion...
✅ Chat completion successful!
Response: The capital of France is Paris.
🔄 Testing document analysis capability...
✅ Document analysis successful!
Analysis: Yes, this policy covers knee surgery with 80% coverage after meeting the $1,500 annual deductible.
🎉 OpenRouter/DeepSeek integration test completed successfully!
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Run the Application

```bash
uvicorn app.main:app --reload
```

## Model Information

### DeepSeek R1 (deepseek/deepseek-r1-0528:free)

- **Type**: Free tier model via OpenRouter
- **Strengths**: 
  - Excellent reasoning capabilities
  - Good at document analysis
  - Strong performance on complex queries
  - Free usage tier available
- **Use Cases**: 
  - Insurance policy analysis
  - Legal document interpretation
  - HR policy queries
  - Compliance document review

## API Compatibility

The system uses the OpenAI-compatible API format, so switching between OpenRouter and OpenAI is seamless. Just change these environment variables:

### For OpenRouter (DeepSeek):
```env
OPENAI_API_KEY=sk-or-your-openrouter-key
OPENAI_MODEL=deepseek/deepseek-r1-0528:free
OPENAI_BASE_URL=https://openrouter.ai/api/v1
```

### For OpenAI (if you want to switch back):
```env
OPENAI_API_KEY=sk-your-openai-key
OPENAI_MODEL=gpt-4-turbo-preview
OPENAI_BASE_URL=https://api.openai.com/v1
```

## Troubleshooting

### Common Issues

1. **"Invalid API Key" Error**
   - Verify your OpenRouter API key is correct
   - Ensure it starts with `sk-or-`
   - Check your OpenRouter account has sufficient credits

2. **"Model not found" Error**
   - Verify the model name: `deepseek/deepseek-r1-0528:free`
   - Check if the model is available in your OpenRouter account
   - Try alternative models like `deepseek/deepseek-chat`

3. **Rate Limit Errors**
   - Free tier has usage limits
   - Consider upgrading your OpenRouter plan
   - Implement retry logic with backoff

4. **Connection Timeout**
   - Check your internet connection
   - Verify OpenRouter service status
   - Try increasing timeout values in the code

### Alternative Models

If the free DeepSeek model doesn't work, try these alternatives:

```env
# Other DeepSeek variants
OPENAI_MODEL=deepseek/deepseek-chat

# Other free/low-cost models on OpenRouter
OPENAI_MODEL=microsoft/wizardlm-2-8x22b
OPENAI_MODEL=meta-llama/llama-3.1-8b-instruct:free
```

## Performance Considerations

### DeepSeek Model Performance

- **Response Time**: Generally 2-5 seconds per query
- **Context Length**: Supports long documents (up to 32k tokens)
- **Accuracy**: High accuracy for document analysis tasks
- **Cost**: Free tier available, paid tiers very cost-effective

### Optimization Tips

1. **Chunk Size**: Keep document chunks under 2000 tokens for best performance
2. **Temperature**: Use low temperature (0.1-0.3) for factual document analysis
3. **Max Tokens**: Set appropriate limits (200-500 tokens) for responses
4. **Caching**: Consider caching responses for repeated queries

## Monitoring Usage

1. Check your OpenRouter dashboard for usage statistics
2. Monitor API response times and error rates
3. Set up alerts for quota limits
4. Track costs if using paid tiers

## Support

- **OpenRouter Documentation**: https://openrouter.ai/docs
- **DeepSeek Model Info**: Check OpenRouter model catalog
- **Community**: OpenRouter Discord/forums
- **Issues**: Report system-specific issues in this project's repository

## Next Steps

Once your OpenRouter setup is working:

1. Upload test documents via the API
2. Try sample queries from different domains
3. Explore the interactive API documentation at `/docs`
4. Configure PostgreSQL and Pinecone for full functionality
5. Deploy to production with proper security measures
