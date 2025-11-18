import { SERVER_URL } from '$lib/constants';

export interface WorkflowListResponse {
	workflows: string[];
}

export class WorkflowService {
	/**
	 * 사용 가능한 워크플로우 목록을 가져옵니다
	 */
	async getWorkflowList(): Promise<string[]> {
		const response = await fetch(`${SERVER_URL}/workflows`);

		if (!response.ok) {
			throw new Error(`서버 응답 에러: ${response.status} ${response.statusText}`);
		}

		const data: WorkflowListResponse = await response.json();
		return data.workflows || [];
	}
}

export const workflowService = new WorkflowService();
