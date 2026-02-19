#!/bin/bash

# Replace all emojis with Material Icons in frontend files

echo "Replacing emojis with Material Icons..."

# ResultsPage.jsx
sed -i '' 's/<div style={{ fontSize: 48, marginBottom: 16 }}>📋<\/div>/<span className="material-symbols-outlined" style={{ fontSize: 48, marginBottom: 16, color: "var(--text-dim)" }}>description<\/span>/g' frontend/src/pages/ResultsPage.jsx
sed -i '' 's/← Back to Dashboard/<span className="material-symbols-outlined" style={{fontSize: "16px", marginRight: "4px"}}>arrow_back<\/span> Back to Dashboard/g' frontend/src/pages/ResultsPage.jsx
sed -i '' 's/📋 Raw Test Output/<span className="material-symbols-outlined" style={{fontSize: "16px", marginRight: "6px"}}>code<\/span> Raw Test Output/g' frontend/src/pages/ResultsPage.jsx
sed -i '' 's/{isRunning ? `⏳ ${run.current_agent || run.status}` : passed ? "✓ PASSED" : "✗ FAILED"}/{isRunning ? <><span className="material-symbols-outlined rift-spinner" style={{fontSize: "16px", marginRight: "4px"}}>progress_activity<\/span> {run.current_agent || run.status}</> : passed ? <><span className="material-symbols-outlined" style={{fontSize: "16px", marginRight: "4px"}}>check_circle<\/span> PASSED</> : <><span className="material-symbols-outlined" style={{fontSize: "16px", marginRight: "4px"}}>cancel<\/span> FAILED</>}/g' frontend/src/pages/ResultsPage.jsx
sed -i '' 's/🌿 /<span className="material-symbols-outlined" style={{fontSize: "14px", marginRight: "4px"}}>account_tree<\/span> /g' frontend/src/pages/ResultsPage.jsx
sed -i '' 's/📄 /<span className="material-symbols-outlined" style={{fontSize: "14px", marginRight: "4px"}}>description<\/span> /g' frontend/src/pages/ResultsPage.jsx

# Dashboard.jsx  
sed -i '' 's/⚡/⚡/g' frontend/src/pages/Dashboard.jsx
sed -i '' 's/📊/<span className="material-symbols-outlined">analytics<\/span>/g' frontend/src/pages/Dashboard.jsx
sed -i '' 's/🔧/<span className="material-symbols-outlined">build<\/span>/g' frontend/src/pages/Dashboard.jsx
sed -i '' 's/⏱/<span className="material-symbols-outlined">schedule<\/span>/g' frontend/src/pages/Dashboard.jsx
sed -i '' 's/📈/<span className="material-symbols-outlined">trending_up<\/span>/g' frontend/src/pages/Dashboard.jsx

echo "✓ Done!"
