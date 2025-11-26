include .env
export

deploy:
	gcloud run deploy ${AGENT_SERVICE_NAME} \
		--source . \
		--region ${GOOGLE_CLOUD_LOCATION} \
		--project ${GOOGLE_CLOUD_PROJECT} \
		--allow-unauthenticated \
		--set-env-vars="GOOGLE_CLOUD_PROJECT=${GOOGLE_CLOUD_PROJECT},GOOGLE_CLOUD_LOCATION=${GOOGLE_CLOUD_LOCATION},GOOGLE_GENAI_USE_VERTEXAI=${GOOGLE_GENAI_USE_VERTEXAI}"
		# Agrega cualquier otra variable de entorno necesaria para tu agente

delete:
	gcloud run services delete ${AGENT_SERVICE_NAME} --region ${GOOGLE_CLOUD_LOCATION} 