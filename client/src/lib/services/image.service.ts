import { SERVER_URL, WORKFLOW_FILE } from '../constants';

export interface ImageGenerationRequest {
	prompt: string | object;
	workflow: string;
	subfolder: string;
}

export interface ImageGenerationResponse {
	image_urls: string[];
}

export class ImageService {
	async generateImage(request: ImageGenerationRequest): Promise<ImageGenerationResponse> {
		const response = await fetch(`${SERVER_URL}/generate`, {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify(request)
		});

		if (!response.ok) {
			throw new Error('이미지 서버와의 연결에 실패했습니다.');
		}

		return response.json();
	}

	createRequestBody(prompt: string, subfolder: string, workflow: string = WORKFLOW_FILE): ImageGenerationRequest {
		try {
			const jsonData = JSON.parse(prompt);

			if (jsonData?.event && Array.isArray(jsonData.event)) {
				return {
					prompt: jsonData,
					workflow,
					subfolder
				};
			}

			throw new Error('올바른 JSON 형식이 아닙니다.');
		} catch {
			return {
				workflow,
				prompt,
				subfolder
			};
		}
	}

	validateImageUrls(imageUrls: string[]): string[] {
		return imageUrls.filter((url) => url !== 'timeout');
	}
}

export const imageService = new ImageService();
