// MediQuery AI Frontend Engine

document.addEventListener("DOMContentLoaded", () => {
    // Elements
    const chatForm = document.getElementById("chat-form");
    const queryInput = document.getElementById("query-input");
    const chatMessages = document.getElementById("chat-messages");
    const logsBody = document.getElementById("logs-body");
    
    // Stats elements
    const statPatients = document.querySelector("#stat-patients .stat-value");
    const statAdmissions = document.querySelector("#stat-admissions .stat-value");
    const statDoctors = document.querySelector("#stat-doctors .stat-value");
    const statBilling = document.querySelector("#stat-billing .stat-value");
    
    // Pipeline elements
    const stepQuery = document.getElementById("step-query");
    const stepOrchestrator = document.getElementById("step-orchestrator");
    const stepAgent = document.getElementById("step-agent");
    const stepAgentIcon = document.getElementById("step-agent-icon");
    const stepAgentName = document.getElementById("step-agent-name");
    const stepResponse = document.getElementById("step-response");
    const pipelineStatus = document.getElementById("pipeline-status");

    // Initialize Page
    fetchStats();
    fetchLogs();

    // Event listener for chat submissions
    chatForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const query = queryInput.value.trim();
        if (!query) return;
        
        queryInput.value = "";
        
        // Append user query to chat
        appendUserMessage(query);
        
        // Run visual pipeline tracing
        await runPipelineTrace(query);
    });

    // Event listener for recommended queries
    document.querySelectorAll(".sample-query-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            const query = btn.getAttribute("data-query");
            queryInput.value = query;
            chatForm.dispatchEvent(new Event("submit"));
        });
    });

    // Helper functions
    function appendUserMessage(text) {
        const msgDiv = document.createElement("div");
        msgDiv.className = "message user";
        msgDiv.innerHTML = `
            <div class="avatar"><i class="fa-solid fa-user"></i></div>
            <div class="message-content">
                <p>${escapeHtml(text)}</p>
                <div class="message-meta">${getCurrentTime()}</div>
            </div>
        `;
        chatMessages.appendChild(msgDiv);
        scrollToBottom();
    }

    function appendAssistantMessage(data) {
        const msgDiv = document.createElement("div");
        msgDiv.className = "message assistant";
        
        let metaContent = `
            <span class="agent-badge ${data.route.toLowerCase()}">${data.route} Agent</span>
            • Latency: ${data.latency_ms} ms
        `;
        
        let innerHTML = `
            <div class="avatar"><i class="fa-solid fa-robot"></i></div>
            <div class="message-content">
                <div class="text-answer">${formatMarkdownText(data.response)}</div>
        `;
        
        // Add SQL dropdown if SQL query was executed
        if (data.route === "SQL" && data.sql) {
            const uniqueId = "sql-" + Math.floor(Math.random() * 1000000);
            innerHTML += `
                <div class="sql-toggle">
                    <button class="sql-toggle-btn" onclick="toggleSqlDisplay('${uniqueId}')">
                        <i class="fa-solid fa-code"></i> View Generated SQL
                    </button>
                    <pre class="sql-code" id="${uniqueId}">${escapeHtml(data.sql)}</pre>
                </div>
            `;
        }
        
        // Add citations if RAG was run
        if (data.route === "RAG" && data.citations && data.citations.length > 0) {
            innerHTML += `
                <div class="citations-list">
                    <strong>Reference chunks retrieved:</strong>
                    <ul>
                        ${data.citations.map(c => `
                            <li>
                                <em>"${escapeHtml(c.text.substring(0, 100))}..."</em> 
                                <br><span style="color:#a78bfa;">[Source: ${escapeHtml(c.source)} • Rel: ${Math.round(c.score * 100)}%]</span>
                            </li>
                        `).join('')}
                    </ul>
                </div>
            `;
        }
        
        innerHTML += `
                <div class="message-meta">${metaContent} • ${data.timestamp}</div>
            </div>
        `;
        
        msgDiv.innerHTML = innerHTML;
        chatMessages.appendChild(msgDiv);
        scrollToBottom();
    }

    // Trace Orchestrator and agent steps on the visual flow diagram
    async function runPipelineTrace(query) {
        // Reset pipeline steps visual highlight
        resetPipelineSteps();
        
        // Step 1: User Query Active
        stepQuery.classList.add("active");
        pipelineStatus.innerHTML = `Analyzing input query: "<em>${escapeHtml(query)}</em>"`;
        
        await sleep(400);
        
        // Step 2: Orchestrator active
        stepOrchestrator.classList.add("active");
        pipelineStatus.innerHTML = `Orchestrator Agent routing query and detecting intent...`;
        
        try {
            // Trigger API request
            const response = await fetch("/api/query", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ query: query })
            });
            
            const data = await response.json();
            
            await sleep(400);
            
            // Step 3: Selected Agent active
            stepAgent.className = `flow-step active ${data.route.toLowerCase()}-mode`;
            if (data.route === "SQL") {
                stepAgentIcon.innerHTML = `<i class="fa-solid fa-database"></i>`;
                stepAgentName.innerText = "NLP-to-SQL Agent";
                pipelineStatus.innerHTML = `Routed to **NLP-to-SQL Agent**. Translating and executing SQL query on SQLite database...`;
            } else if (data.route === "RAG") {
                stepAgentIcon.innerHTML = `<i class="fa-solid fa-folder-open"></i>`;
                stepAgentName.innerText = "RAG Agent";
                pipelineStatus.innerHTML = `Routed to **RAG Agent**. Querying local document vector index and synthesizing policy rules...`;
            } else {
                stepAgentIcon.innerHTML = `<i class="fa-solid fa-comments"></i>`;
                stepAgentName.innerText = "General Agent";
                pipelineStatus.innerHTML = `Routed to **General Agent** for conversational greetings or help.`;
            }
            
            await sleep(400);
            
            // Step 4: Response Formatter active
            stepResponse.classList.add("active");
            pipelineStatus.innerHTML = `Response Formatter generating user-friendly output layout (Latency: ${data.latency_ms} ms).`;
            
            // Append assistant response to chat
            appendAssistantMessage(data);
            
            // Update stats in case counts changed (though read-only queries usually, good for UI refresh)
            fetchStats();
            
            // Update Log table
            fetchLogs();
            
        } catch (err) {
            console.error(err);
            pipelineStatus.innerHTML = `<span style="color:#ef4444;">Pipeline Execution Error: ${escapeHtml(err.message)}</span>`;
            const errorResponse = {
                route: "GENERAL",
                response: `I'm sorry, I was unable to connect to the backend system. Please ensure the FastAPI server is running.`,
                latency_ms: 0,
                timestamp: getCurrentTime()
            };
            appendAssistantMessage(errorResponse);
        }
    }

    function resetPipelineSteps() {
        stepQuery.className = "flow-step";
        stepOrchestrator.className = "flow-step";
        stepAgent.className = "flow-step";
        stepAgentIcon.innerHTML = `<i class="fa-solid fa-robot"></i>`;
        stepAgentName.innerText = "Selected Agent";
        stepResponse.className = "flow-step";
    }

    // API Fetches
    async function fetchStats() {
        try {
            const res = await fetch("/api/db-stats");
            const stats = await res.json();
            
            if (stats.error) {
                console.error("Database stats error:", stats.error);
                return;
            }
            
            statPatients.innerText = Number(stats.total_patients).toLocaleString();
            statAdmissions.innerText = Number(stats.total_admissions).toLocaleString();
            statDoctors.innerText = Number(stats.total_doctors).toLocaleString();
            statBilling.innerText = `$${Math.round(stats.avg_billing).toLocaleString()}`;
        } catch (err) {
            console.error("Failed to fetch database stats", err);
        }
    }

    async function fetchLogs() {
        try {
            const res = await fetch("/api/logs");
            const logs = await res.json();
            
            if (!logs || logs.length === 0) {
                logsBody.innerHTML = `<tr><td colspan="4" class="empty-log">No recent routing decisions.</td></tr>`;
                return;
            }
            
            // Display last 10 logs descending
            logsBody.innerHTML = logs.slice(-10).reverse().map(log => `
                <tr>
                    <td>${log.timestamp.substring(11)}</td>
                    <td class="query-cell" title="${escapeHtml(log.query)}">${escapeHtml(log.query)}</td>
                    <td><span class="log-route ${log.route.toLowerCase()}">${log.route}</span></td>
                    <td>${log.latency_ms} ms</td>
                </tr>
            `).join('');
        } catch (err) {
            console.error("Failed to fetch logs", err);
        }
    }

    // Helper functions
    function escapeHtml(text) {
        if (!text) return "";
        return text
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    function formatMarkdownText(text) {
        if (!text) return "";
        let formatted = text;
        
        // Bold formatting
        formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        
        // Inline code formatting
        formatted = formatted.replace(/`(.*?)`/g, '<code>$1</code>');
        
        // Code block formatting
        formatted = formatted.replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>');
        
        // Bullet list formatting
        formatted = formatted.replace(/^\*\s(.*)$/gm, '<li>$1</li>');
        formatted = formatted.replace(/^\-\s(.*)$/gm, '<li>$1</li>');
        
        // Wrap contiguous list items in <ul>
        formatted = formatted.replace(/(<li>.*?<\/li>)+/g, '<ul>$&</ul>');
        
        // Handle newlines as paragraphs/breaks, but not inside tables/lists
        formatted = formatted.replace(/\n\n/g, '<br><br>');
        
        // Simple Markdown Table conversion (for database outputs if any)
        if (formatted.includes('|')) {
            const lines = formatted.split('\n');
            let inTable = false;
            let tableHtml = '<div class="table-wrapper"><table class="result-table">';
            
            for (let line of lines) {
                if (line.trim().startsWith('|')) {
                    if (!inTable) {
                        inTable = true;
                        tableHtml += '<thead>';
                    }
                    const cols = line.split('|').map(c => c.trim()).filter((c, i, a) => i > 0 && i < a.length - 1);
                    if (line.includes('---')) {
                        tableHtml += '</thead><tbody>';
                    } else {
                        tableHtml += '<tr>' + cols.map(c => inTable ? `<th>${c}</th>` : `<td>${c}</td>`).join('') + '</tr>';
                    }
                } else if (inTable) {
                    inTable = false;
                    tableHtml += '</tbody></table></div>';
                    tableHtml += line;
                } else {
                    tableHtml += line + '\n';
                }
            }
            if (inTable) {
                tableHtml += '</tbody></table></div>';
            }
            formatted = tableHtml;
        }
        
        return formatted;
    }

    function getCurrentTime() {
        const d = new Date();
        return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    }

    function sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    function scrollToBottom() {
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
});

// Global SQL display toggle function
function toggleSqlDisplay(elementId) {
    const codeEl = document.getElementById(elementId);
    if (codeEl.style.display === "block") {
        codeEl.style.display = "none";
    } else {
        codeEl.style.display = "block";
    }
}
