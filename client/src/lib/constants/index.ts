import type { SelectOption } from '../types';

export const WORKFLOW_FILE = 'dungeon_background.json';
export const SERVER_URL = 'http://127.0.0.1:5000';
export const BATCH_DELAY = 500;
export const PROGRESS_UPDATE_INTERVAL = 2;
export const SMALL_BATCH_THRESHOLD = 100;

export const EVENT_COUNT_OPTIONS: SelectOption[] = [
	{ value: '1', label: '1개' },
	{ value: '5', label: '5개' },
	{ value: '10', label: '10개' },
	{ value: '20', label: '20개' },
	{ value: '50', label: '50개' },
	{ value: '100', label: '100개' },
	{ value: '200', label: '200개' },
	{ value: '500', label: '500개' },
	{ value: '1000', label: '1,000개' },
	{ value: '5000', label: '5,000개' },
	{ value: '10000', label: '10,000개' }
];

export const BATCH_SIZE_OPTIONS: SelectOption[] = [
	{ value: '5', label: '5개' },
	{ value: '10', label: '10개' },
	{ value: '20', label: '20개' },
	{ value: '50', label: '50개' }
];
