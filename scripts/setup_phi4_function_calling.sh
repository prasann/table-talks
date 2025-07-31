#!/bin/bash

# Setup script for Phi-4-mini with function calling support

echo "🚀 Setting up Phi-4-mini for function calling..."

# Step 1: Pull the Phi-4-mini model
echo "📥 Pulling phi4-mini:3.8b-fp16 model..."
ollama pull phi4-mini:3.8b-fp16

# Step 2: Create Modelfile with proper template
echo "📝 Creating Modelfile with function calling template..."

cat > /tmp/Modelfile << 'EOF'
FROM phi4-mini:3.8b-fp16

TEMPLATE """
{{- if .Messages }}
{{- if or .System .Tools }}<|system|>

{{ if .System }}{{ .System }}
{{- end }}
In addition to plain text responses, you can chose to call one or more of the provided functions.

Use the following rule to decide when to call a function:
  * if the response can be generated from your internal knowledge (e.g., as in the case of queries like "What is the capital of Poland?"), do so
  * if you need external information that can be obtained by calling one or more of the provided functions, generate a function calls

If you decide to call functions:
  * prefix function calls with functools marker (no closing marker required)
  * all function calls should be generated in a single JSON list formatted as functools[{"name": [function name], "arguments": [function arguments as JSON]}, ...]
  * follow the provided JSON schema. Do not hallucinate arguments or values. Do to blindly copy values from the provided samples
  * respect the argument type formatting. E.g., if the type if number and format is float, write value 7 as 7.0
  * make sure you pick the right functions that match the user intent

Available functions as JSON spec:
{{- if .Tools }}
{{ .Tools }}
{{- end }}<|end|>
{{- end }}
{{- range .Messages }}
{{- if ne .Role "system" }}<|{{ .Role }}|>
{{- if and .Content (eq .Role "tools") }}

{"result": {{ .Content }}}
{{- else if .Content }}

{{ .Content }}
{{- else if .ToolCalls }}

functools[
{{- range .ToolCalls }}{{ "{" }}"name": "{{ .Function.Name }}", "arguments": {{ .Function.Arguments }}{{ "}" }}
{{- end }}]
{{- end }}<|end|>
{{- end }}
{{- end }}<|assistant|>

{{ else }}
{{- if .System }}<|system|>

{{ .System }}<|end|>{{ end }}{{ if .Prompt }}<|user|>

{{ .Prompt }}<|end|>{{ end }}<|assistant|>

{{ end }}{{ .Response }}{{ if .Response }}<|user|>{{ end }}
"""
EOF

# Step 3: Create the model with the new template
echo "🔧 Creating model with function calling template..."
ollama create phi4-mini-fc -f /tmp/Modelfile

# Step 4: Verify the model was created
echo "✅ Verifying model creation..."
if ollama list | grep -q "phi4-mini-fc"; then
    echo "✅ phi4-mini-fc model created successfully!"
    echo ""
    echo "🎉 Setup complete! You can now use:"
    echo "   Model: phi4-mini-fc"
    echo "   Features: Native function calling support"
    echo ""
    echo "💡 Update your config.yaml to use: model: 'phi4-mini-fc'"
else
    echo "❌ Model creation failed. Please check the output above."
    exit 1
fi

# Cleanup
rm /tmp/Modelfile

echo "🏁 Ready to use native function calling with TableTalk!"
