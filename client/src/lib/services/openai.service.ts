// openai.service.ts
import type { EventData } from '../types';
import { SERVER_URL } from '../constants';

export class OpenAIService {
	private isAvailable = false;

	initialize() {
		// 서버 측에서 OpenAI를 처리하므로 클라이언트 초기화는 필요 없음
		// 서버 연결 가능 여부만 확인
		this.isAvailable = true;
	}

	async generateSingleEvent(category: string): Promise<EventData | null> {
		try {
			const response = await fetch(`${SERVER_URL}/generate-event`, {
				method: 'POST',
				headers: {
					'Content-Type': 'application/json'
				},
				body: JSON.stringify({ category })
			});

			if (!response.ok) {
				const errorData = await response.json();
				throw new Error(errorData.error || 'Failed to generate event');
			}

			const eventData: EventData = await response.json();
			return eventData;
		} catch (err) {
			console.error('Error generating event:', err);
			throw err;
		}
	}

	isInitialized(): boolean {
		return this.isAvailable;
	}
}

export const openAIService = new OpenAIService();

// format.utils.ts에 추가할 함수들
export function formatEventsAsJson(events: EventData[]): string {
	// events 배열을 event 키로 래핑
	const wrappedData = {
		event: events
	};
	return JSON.stringify(wrappedData, null, 2);
}

export function formatEventsAsJsonWithMetadata(events: EventData[]): string {
	const wrappedData = {
		meta: {
			total: events.length,
			generated_at: new Date().toISOString()
		},
		event: events
	};
	return JSON.stringify(wrappedData, null, 2);
}
