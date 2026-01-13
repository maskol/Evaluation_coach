// Flow Health Check - Dynamic content loader
// Replaces hardcoded content with RAG-based knowledge base

async function fetchFlowHealthCheckContent(filterInfo) {
    try {
        const response = await fetch(`${API_BASE_URL}/v1/flow-health-check`);

        if (!response.ok) {
            throw new Error('Failed to load Flow Health Check content');
        }

        const data = await response.json();
        renderFlowHealthCheckContent(data, filterInfo);

    } catch (error) {
        console.error('Error loading Flow Health Check:', error);
        const flowhealthContent = document.getElementById('flowhealthContent');
        if (flowhealthContent) {
            flowhealthContent.innerHTML = `
                <div class="messages" style="padding: 20px;">
                    <div style="background: #FEE2E2; border: 2px solid #EF4444; border-radius: 8px; padding: 20px; text-align: center;">
                        <div style="font-size: 36px; margin-bottom: 12px;">⚠️</div>
                        <h3 style="color: #DC2626; margin: 0 0 8px 0;">Error Loading Content</h3>
                        <p style="color: #991B1B; margin: 0;">${error.message}</p>
                        <p style="color: #666; margin: 12px 0 0 0; font-size: 14px;">Please check that the backend is running and the knowledge base file exists.</p>
                    </div>
                </div>
            `;
        }
    }
}

function renderFlowHealthCheckContent(data, filterInfo) {
    const flowhealthContent = document.getElementById('flowhealthContent');
    if (!flowhealthContent) return;

    const quickTest = data.quick_test || {};
    const categories = data.categories || [];
    const flowSmells = data.flow_smells || {};

    flowhealthContent.innerHTML = `
        <div class="messages" style="padding: 20px;">
            <div class="active-context-inline">
                <div class="active-context-title-inline">📊 Active Context</div>
                <div class="active-context-content-inline">
                    ${filterInfo}
                </div>
            </div>

            <div style="background: white; border-radius: 8px; padding: 30px; margin-top: 20px;">
                <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 24px;">
                    <div style="font-size: 36px;">🏥</div>
                    <div>
                        <h2 style="margin: 0; color: #333;">Flow Health Check</h2>
                        <p style="margin: 4px 0 0 0; color: #666; font-size: 14px;">Diagnose flow problems through systematic questioning</p>
                        <p style="margin: 4px 0 0 0; color: #999; font-size: 12px; font-style: italic;">📝 Content loaded from knowledge base</p>
                    </div>
                </div>

                ${quickTest.questions ? `
                <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 8px; padding: 20px; margin-bottom: 24px; color: white;">
                    <h3 style="margin: 0 0 12px 0; display: flex; align-items: center; gap: 8px;">
                        <span>🧠</span> ${quickTest.title || 'One-Minute Flow Health Test'}
                    </h3>
                    <p style="margin: 0 0 16px 0; opacity: 0.9; font-size: 14px;">Answer these three questions to quickly assess if flow is under control:</p>
                    <div style="background: rgba(255,255,255,0.15); border-radius: 6px; padding: 16px; display: grid; gap: 12px;">
                        ${quickTest.questions.map((q, i) => `
                            <div style="display: flex; align-items: start; gap: 8px;">
                                <span style="font-weight: bold; min-width: 20px;">${i + 1}.</span>
                                <span>${q}</span>
                            </div>
                        `).join('')}
                    </div>
                    <p style="margin: 16px 0 0 0; font-size: 13px; font-style: italic; opacity: 0.9;">
                        ⚠️ ${quickTest.warning || 'If people can\'t answer → flow is not under control'}
                    </p>
                </div>
                ` : ''}

                <div class="flow-diagnostic-categories">
                    ${categories.map((cat, idx) => renderFlowDiagnosticCategoryFromData(cat, idx + 1)).join('')}
                </div>

                ${flowSmells.bad && flowSmells.good ? `
                <div style="background: #FFF9E6; border: 2px solid #FFD700; border-radius: 8px; padding: 20px; margin-top: 24px;">
                    <h3 style="margin: 0 0 16px 0; color: #D97706; display: flex; align-items: center; gap: 8px;">
                        <span>🚨</span> Flow Smell Checklist (Fast Diagnosis)
                    </h3>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
                        <div>
                            <h4 style="margin: 0 0 8px 0; color: #DC2626; font-size: 14px;">❌ Bad Flow Indicators:</h4>
                            <ul style="margin: 0; padding-left: 20px; font-size: 14px; color: #333;">
                                ${flowSmells.bad.map(phrase => `<li>${phrase}</li>`).join('')}
                            </ul>
                        </div>
                        <div>
                            <h4 style="margin: 0 0 8px 0; color: #059669; font-size: 14px;">✅ Good Flow Indicators:</h4>
                            <ul style="margin: 0; padding-left: 20px; font-size: 14px; color: #333;">
                                ${flowSmells.good.map(phrase => `<li>${phrase}</li>`).join('')}
                            </ul>
                        </div>
                    </div>
                </div>
                ` : ''}
            </div>
        </div>
    `;
}

function renderFlowDiagnosticCategoryFromData(category, index) {
    const questions = category.questions || [];
    const good = category.good || '';
    const bad = category.bad || '';

    const emoji = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣'][index - 1] || `${index}️⃣`;

    return `
        <div class="flow-diagnostic-card" style="background: white; border: 1px solid #e5e7eb; border-radius: 8px; padding: 20px; margin-bottom: 16px;">
            <div style="margin-bottom: 16px;">
                <h3 style="margin: 0 0 4px 0; color: #333; font-size: 18px;">${emoji} ${category.title || ''}</h3>
                <p style="margin: 0; color: #667eea; font-weight: 600; font-size: 14px;">${category.subtitle || ''}</p>
            </div>
            
            <div style="background: #F9FAFB; border-radius: 6px; padding: 16px; margin-bottom: 16px;">
                <h4 style="margin: 0 0 12px 0; color: #666; font-size: 13px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">Probing Questions:</h4>
                <ul style="margin: 0; padding-left: 20px; display: grid; gap: 8px;">
                    ${questions.map(q => `<li style="color: #333; font-size: 14px;">${q}</li>`).join('')}
                </ul>
            </div>
            
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
                <div style="background: #ECFDF5; border-left: 3px solid #10B981; padding: 12px; border-radius: 4px;">
                    <div style="font-weight: 600; color: #059669; font-size: 13px; margin-bottom: 4px;">✅ Good Flow:</div>
                    <div style="color: #065F46; font-size: 13px;">${good}</div>
                </div>
                <div style="background: #FEF2F2; border-left: 3px solid #EF4444; padding: 12px; border-radius: 4px;">
                    <div style="font-weight: 600; color: #DC2626; font-size: 13px; margin-bottom: 4px;">❌ Bad Flow:</div>
                    <div style="color: #991B1B; font-size: 13px;">${bad}</div>
                </div>
            </div>
        </div>
    `;
}
