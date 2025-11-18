export interface EventData {
	tags: string;
	background_image: string;
}

export interface GenerationConfig {
	eventCount: string;
	batchSize: string;
}

export interface GenerationState {
	isGenerating: boolean;
	isLoading: boolean;
	currentBatch: number;
	totalEvents: number;
	progressPercent: number;
	allResults: EventData[];
}

export interface ImageState {
	imageUrl: string;
	generatedImages: string[];
	showMultipleImages: boolean;
	isGenerating: boolean;
}

export interface ErrorState {
	errorMessage: string;
	fileErrorMessage: string;
}

export interface SelectOption {
	value: string;
	label: string;
}
