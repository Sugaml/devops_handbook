{{- define "hooks-demo.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{- define "hooks-demo.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name (include "hooks-demo.name" .) | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}

{{- define "hooks-demo.labels" -}}
helm.sh/chart: {{ .Chart.Name }}-{{ .Chart.Version }}
app.kubernetes.io/name: {{ include "hooks-demo.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{- define "hooks-demo.selectorLabels" -}}
app.kubernetes.io/name: {{ include "hooks-demo.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}
