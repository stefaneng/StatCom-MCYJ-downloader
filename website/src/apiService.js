// OpenRouter API service for DeepSeek queries

/**
 * Submit a query to DeepSeek v3.2 via OpenRouter
 * @param {string} apiKey - The OpenRouter API key
 * @param {string} query - The user's query
 * @param {string} documentText - The full document text (pages concatenated)
 * @returns {Promise<Object>} Response with {response, inputTokens, outputTokens, cost}
 */
export async function queryDeepSeek(apiKey, query, documentText) {
    const startTime = performance.now();
    
    // Combine query with document as specified
    const fullPrompt = `${query}\n\n${documentText}`;
    
    const response = await fetch('https://openrouter.ai/api/v1/chat/completions', {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${apiKey}`,
            'Content-Type': 'application/json',
            'HTTP-Referer': window.location.href,
            'X-Title': 'MCYJ Datapipeline Document Viewer'
        },
        body: JSON.stringify({
            model: 'deepseek/deepseek-v3.2',
            messages: [
                {
                    role: 'user',
                    content: fullPrompt
                }
            ],
            usage: {
                include: true
            }
        })
    });

    const endTime = performance.now();
    const durationMs = Math.round(endTime - startTime);

    if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.error?.message || `API request failed: ${response.statusText}`);
    }

    const data = await response.json();
    
    // Extract response and token usage
    const aiResponse = data.choices?.[0]?.message?.content || 'No response received';
    const usage = data.usage || {};
    const inputTokens = usage.prompt_tokens || 0;
    const outputTokens = usage.completion_tokens || 0;
    
    // Extract cost from usage object (OpenRouter returns it here with usage accounting enabled)
    const cost = usage.cost || null;

    return {
        response: aiResponse,
        inputTokens,
        outputTokens,
        cost,
        durationMs
    };
}
