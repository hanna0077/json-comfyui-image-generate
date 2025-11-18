<script lang="ts">
	import { onMount } from 'svelte';
	import { writable } from 'svelte/store';
	import { page } from '$app/stores';
	import { get } from 'svelte/store';
	import { goto } from '$app/navigation';

	let workflow = '';
	let imageUrl = '';
	let prompt: string = '';
	let subfolder = '';
	let errorMessage = '';
	let fileErrorMessage = '';
	let uploadStatus = '';
	let arr = writable<any[]>([]);
	let isGenerating = false;
	let generatedImages: string[] = [];
	let showMultipleImages = false;
	let inputMethod: 'none' | 'file' | 'manual' = 'none';

	const eyeLeft = writable({ x: 0, y: 0 });
	const eyeRight = writable({ x: 0, y: 0 });

	let container: HTMLElement;
	let eyeRadius = 6;
	let eyeCenterLeft: { x: number; y: number };
	let eyeCenterRight: { x: number; y: number };

	function setIsGenerating(value: boolean) {
		isGenerating = value;
		localStorage.setItem('isGenerating', value ? 'true' : 'false');
	}

	onMount(() => {
		const saved = localStorage.getItem('isGenerating');
		isGenerating = saved === 'true'; // 저장된 값이 있으면 복원

		// generatedJSON이 있으면 prompt에 로드
		const generatedJSON = localStorage.getItem('generatedJSON');
		if (generatedJSON) {
			prompt = generatedJSON;
			inputMethod = 'manual';
			// 사용 후 제거
			localStorage.removeItem('generatedJSON');
		}
	});

	function updateEyePosition(event: MouseEvent) {
		const { clientX, clientY } = event;

		const moveEye = (center: { x: number; y: number }) => {
			const dx = clientX - center.x;
			const dy = clientY - center.y;
			const angle = Math.atan2(dy, dx);

			return {
				x: Math.cos(angle) * eyeRadius,
				y: Math.sin(angle) * eyeRadius
			};
		};

		eyeLeft.set(moveEye(eyeCenterLeft));
		eyeRight.set(moveEye(eyeCenterRight));
	}

	function resetEyes() {
		eyeLeft.set({ x: 0, y: 0 });
		eyeRight.set({ x: 0, y: 0 });
	}

	onMount(() => {
		const rect = container.getBoundingClientRect();
		eyeCenterLeft = {
			x: rect.left + rect.width * 0.35,
			y: rect.top + rect.height * 0.4
		};
		eyeCenterRight = {
			x: rect.left + rect.width * 0.65,
			y: rect.top + rect.height * 0.4
		};

		container.addEventListener('mousemove', updateEyePosition);
		container.addEventListener('mouseleave', resetEyes);

		return () => {
			container.removeEventListener('mousemove', updateEyePosition);
			container.removeEventListener('mouseleave', resetEyes);
		};
	});

	onMount(() => {
		const url = get(page).url;
		workflow = url.searchParams.get('workflow') ?? '';
	});

	async function generate(event: Event) {
		event.preventDefault();
		errorMessage = '';

		// 입력값 검증
		if (!prompt.trim()) {
			errorMessage = '프롬프트를 입력해주세요.';
			return;
		}

		// 생성 요청 정보를 localStorage에 저장
		localStorage.setItem('generationRequest', JSON.stringify({ workflow, prompt, subfolder }));

		// 미리보기 페이지로 이동
		goto('/preview');
	}

	function selectImage(url: string) {
		imageUrl = url;
	}

	async function onFileSelected(event: Event) {
		fileErrorMessage = '';
		uploadStatus = '';
		const input = event.target as HTMLInputElement;
		if (!input.files || input.files.length === 0) {
			fileErrorMessage = '파일을 선택해주세요.';
			inputMethod = 'none';
			return;
		}
		const file = input.files[0];
		const reader = new FileReader();

		reader.onload = async () => {
			try {
				const json = JSON.parse(reader.result as string);
				arr.set(json);

				// JSON 내용을 textarea에 표시
				prompt = JSON.stringify(json, null, 2); // 들여쓰기 포함한 문자열
				inputMethod = 'file';
			} catch (e) {
				fileErrorMessage = 'JSON 파싱에 실패했습니다.';
				console.error(e);
			}
		};

		reader.onerror = () => {
			fileErrorMessage = '파일 읽기에 실패했습니다.';
		};

		reader.readAsText(file);
	}

	function onManualInput() {
		if (prompt.trim() !== '') {
			inputMethod = 'manual';
		} else {
			inputMethod = 'none';
		}
	}

	function clearFileInput() {
		const fileInput = document.querySelector('input[type="file"]') as HTMLInputElement;
		if (fileInput) {
			fileInput.value = '';
		}
		prompt = '';
		inputMethod = 'none';
	}
</script>

<section class="min-h-screen flex items-center justify-center p-4 sm:p-6 py-8">
	<form
		bind:this={container}
		on:submit={generate}
		class="w-full max-w-sm sm:max-w-md md:max-w-lg lg:max-w-2xl xl:max-w-4xl max-h-[95vh] overflow-auto rounded-xl sm:rounded-2xl bg-teal-500 p-4 sm:p-6 shadow-lg outline outline-black/5"
	>
		<div class="rounded-lg sm:rounded-xl bg-teal-600 text-neutral-950">
			<div class="min-h-[200px] w-full rounded-md sm:rounded-lg bg-teal-200 sm:min-h-[250px] md:min-h-[300px]">
				{#if isGenerating}
					<div class="flex h-[200px] items-center justify-center sm:h-[250px] md:h-[300px]">
						<p class="text-sm sm:text-base md:text-lg font-semibold">이미지 생성 중...</p>
					</div>
				{:else if imageUrl}
					<div
						class="mx-auto mt-2 max-h-[300px] w-full overflow-auto text-center sm:mt-4 sm:max-h-[400px] md:max-h-[500px]"
					>
						<img src={imageUrl} alt="생성된 캐릭터 이미지" class="mx-auto w-auto object-contain" />
					</div>

					{#if showMultipleImages && generatedImages.length > 1}
						<div class="mt-2 flex flex-wrap justify-center gap-1 p-1 sm:mt-4 sm:gap-2 sm:p-2">
							{#each generatedImages as url, i}
								<button
									type="button"
									class="cursor-pointer border-none bg-transparent p-0"
									on:click={() => selectImage(url)}
									on:keydown={(e) => {
										if (e.key === 'Enter' || e.key === ' ') {
											e.preventDefault();
											selectImage(url);
										}
									}}
									aria-label={`생성된 이미지 ${i + 1} 선택`}
								>
									<img
										src={url}
										alt={`생성된 이미지 ${i + 1}`}
										class="h-12 w-auto border-2 border-transparent object-cover hover:border-teal-600 sm:h-16"
										class:border-teal-800={url === imageUrl}
									/>
								</button>
							{/each}
						</div>
					{/if}
				{:else}
					<div
						class="relative m-auto h-[200px] w-[200px] sm:h-[250px] sm:w-[250px] md:h-[300px] md:w-[300px]"
					>
						<div
							class="absolute left-[30%] top-[40%] flex h-5 w-5 items-center justify-center overflow-hidden rounded-full bg-white sm:h-6 sm:w-6"
						>
							<div
								class="h-1.5 w-1.5 rounded-full bg-black transition-transform duration-100 sm:h-2 sm:w-2"
								style="transform: translate({$eyeLeft.x}px, {$eyeLeft.y}px)"
							></div>
						</div>
						<div
							class="absolute left-[60%] top-[40%] flex h-5 w-5 items-center justify-center overflow-hidden rounded-full bg-white sm:h-6 sm:w-6"
						>
							<div
								class="h-1.5 w-1.5 rounded-full bg-black transition-transform duration-100 sm:h-2 sm:w-2"
								style="transform: translate({$eyeRight.x}px, {$eyeRight.y}px)"
							></div>
						</div>
						<div
							class="absolute left-[45%] top-[60%] h-0.5 w-3 rounded-full bg-black sm:h-1 sm:w-4"
						></div>

						{#if errorMessage}
							<div class="absolute bottom-2 left-1/2 w-4/5 -translate-x-1/2 transform sm:bottom-4">
								<p
									class="rounded-lg bg-red-500 px-2 py-1 text-center text-xs text-white shadow-lg sm:px-4 sm:py-2 sm:text-sm"
								>
									{errorMessage}
								</p>
							</div>
						{/if}
					</div>
				{/if}
			</div>
		</div>
		<input
			bind:value={subfolder}
			type="text"
			placeholder="폴더이름"
			class="my-2 sm:my-4 w-full rounded-md border-2 border-teal-100 bg-teal-100 p-3 text-base sm:text-base"
		/>

		<div class="my-3 sm:my-4">
			<div class="mb-2 flex items-center justify-between">
				<label for="fileInput" class="text-sm sm:text-base font-semibold">JSON 파일 업로드</label>
				{#if inputMethod !== 'none'}
					<button
						type="button"
						on:click={clearFileInput}
						class="rounded-md bg-red-500 px-2 py-1 sm:px-3 sm:py-1.5 text-xs sm:text-sm text-white hover:bg-red-600 transition-colors"
					>
						초기화
					</button>
				{/if}
			</div>
			<input
				id="fileInput"
				type="file"
				accept=".json"
				on:change={onFileSelected}
				disabled={inputMethod === 'manual'}
				class="w-full text-xs sm:text-sm disabled:cursor-not-allowed disabled:opacity-50"
			/>
			{#if inputMethod === 'manual'}
				<p class="mt-1.5 sm:mt-2 text-xs sm:text-sm text-teal-900">
					직접 입력 모드입니다. 파일 업로드를 사용하려면 초기화하세요.
				</p>
			{/if}
			{#if fileErrorMessage}
				<p class="mt-1.5 sm:mt-2 text-xs sm:text-sm text-red-600 font-medium">{fileErrorMessage}</p>
			{/if}
		</div>

		<div class="my-3 sm:my-4">
			<label for="promptInput" class="mb-2 block text-sm sm:text-base font-semibold"
				>또는 직접 입력</label
			>
			<textarea
				id="promptInput"
				bind:value={prompt}
				on:input={onManualInput}
				placeholder="캐릭터 스타일 입력"
				disabled={inputMethod === 'file'}
				rows="6"
				class="w-full rounded-md border-2 border-teal-100 bg-teal-100 p-3 text-base sm:text-base disabled:cursor-not-allowed disabled:opacity-50 resize-none"
			>
			</textarea>
			{#if inputMethod === 'file'}
				<p class="mt-1.5 sm:mt-2 text-xs sm:text-sm text-teal-900">
					파일 업로드 모드입니다. 직접 입력을 사용하려면 초기화하세요.
				</p>
			{/if}
		</div>
		<div class="flex justify-end mt-4">
			<button
				type="submit"
				class="
				aspect-square w-14 sm:w-16 md:w-18
				-translate-y-1.5 sm:-translate-y-2
				rounded-full bg-red-600
				text-xs sm:text-sm md:text-base font-medium text-white
				shadow-[0_4px_0_0_theme('colors.red.800')] sm:shadow-[0_6px_0_0_theme('colors.red.800')]
				transition-all duration-150 ease-in-out
				hover:translate-y-0 hover:shadow-none
				active:translate-y-0 active:bg-red-700 active:text-white/70 active:shadow-none
				disabled:translate-y-0 disabled:cursor-not-allowed disabled:bg-red-400 disabled:opacity-50 disabled:shadow-none
			"
				disabled={isGenerating}
			>
				{isGenerating ? '생성 중...' : '생성'}
			</button>
		</div>
	</form>
</section>
