<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { get } from 'svelte/store';

	let generatedImages: string[] = [];
	let isGenerating = true;
	let errorMessage = '';
	let currentIndex = 0;
	let pollInterval: number | undefined;

	onMount(async () => {
		// localStorage에서 생성 요청 정보 가져오기
		const requestData = localStorage.getItem('generationRequest');

		if (!requestData) {
			errorMessage = '생성 요청 정보가 없습니다.';
			isGenerating = false;
			return;
		}

		const { workflow, prompt, subfolder } = JSON.parse(requestData);

		// 이미지 생성 시작
		try {
			let response;
			let requestBody;

			try {
				const jsonData = JSON.parse(prompt);

				// 'event' 또는 'events' 배열이 있는지 확인
				if (
					(jsonData && jsonData.event && Array.isArray(jsonData.event)) ||
					(jsonData && jsonData.events && Array.isArray(jsonData.events))
				) {
					// API가 기대하는 형식으로 변환: 'event' -> 'events'
					let apiData = { ...jsonData };
					if (jsonData.event && !jsonData.events) {
						apiData = { events: jsonData.event };
					}

					requestBody = { prompt: apiData, workflow, subfolder };
					console.log('배치 요청:', requestBody);
				} else {
					throw new Error('올바른 JSON 형식이 아닙니다.');
				}
			} catch (parseError) {
				// 일반 텍스트로 처리
				requestBody = { workflow, prompt, subfolder };
				console.log('단일 요청:', requestBody);
			}

			response = await fetch('http://127.0.0.1:5000/generate', {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify(requestBody)
			});

			console.log('Response status:', response.status);
			console.log('Response headers:', response.headers.get('content-type'));

			// Content-Type 확인
			const contentType = response.headers.get('content-type');
			if (!contentType || !contentType.includes('application/json')) {
				const text = await response.text();
				console.error('Non-JSON response:', text);
				throw new Error(`서버가 JSON이 아닌 응답을 반환했습니다: ${text.substring(0, 100)}`);
			}

			const data = await response.json();
			console.log('서버 응답:', data); // 디버깅용 로그

			if (!response.ok) {
				throw new Error(data.error || `서버 오류: ${response.status}`);
			}

			// 단수형(image_url)과 복수형(image_urls) 모두 지원
			let imageUrls: string[] = [];

			if (data.image_url) {
				// 단수형인 경우 배열로 변환
				imageUrls = [data.image_url];
			} else if (data.image_urls && Array.isArray(data.image_urls)) {
				// 복수형인 경우
				imageUrls = data.image_urls;
			}

			console.log('추출된 이미지 URLs:', imageUrls); // 디버깅용 로그

			if (imageUrls.length > 0) {
				// 유효한 URL만 필터링 (timeout, error, empty, invalid 제외)
				const validUrls = imageUrls.filter((url: string) => {
					if (typeof url !== 'string') return false;
					if (url === 'timeout' || url === 'error' || url === 'empty' || url === 'invalid')
						return false;
					return url.startsWith('http://') || url.startsWith('https://');
				});

				console.log('유효한 이미지 URLs:', validUrls); // 디버깅용 로그

				if (validUrls.length > 0) {
					generatedImages = validUrls;
					currentIndex = 0;
				} else {
					throw new Error('유효한 이미지가 생성되지 않았습니다. 다시 시도해주세요.');
				}
			} else if (data.error) {
				throw new Error(`서버 에러: ${data.error}`);
			} else {
				console.error('예상치 못한 응답 구조:', data);
				throw new Error('이미지 생성에 실패했습니다. 응답 형식이 올바르지 않습니다.');
			}
		} catch (error) {
			errorMessage = error instanceof Error ? error.message : '서버와의 연결에 실패했습니다.';
			console.error('에러 상세:', error);
		} finally {
			isGenerating = false;
		}
	});

	onDestroy(() => {
		if (pollInterval) {
			clearInterval(pollInterval);
		}
	});

	function selectImage(index: number) {
		currentIndex = index;
	}

	function goHome() {
		goto('/');
	}

	function downloadImage(url: string, index: number) {
		// ComfyUI API URL을 다운로드 가능한 형태로 변환
		const link = document.createElement('a');
		link.href = url;
		link.download = `generated-image-${index + 1}.png`;
		link.target = '_blank'; // 새 탭에서 열기
		document.body.appendChild(link);
		link.click();
		document.body.removeChild(link);
	}

	// 이미지 로드 에러 핸들링
	function handleImageError(event: Event, index: number) {
		console.error(`이미지 로드 실패 (${index + 1}):`, generatedImages[index]);
		const target = event.target as HTMLImageElement;

		// 재시도 로직 추가 (최대 3번)
		const retryCount = parseInt(target.dataset.retryCount || '0');
		if (retryCount < 3) {
			target.dataset.retryCount = String(retryCount + 1);
			console.log(`이미지 로드 재시도 ${retryCount + 1}/3:`, generatedImages[index]);

			// 1초 후 재시도
			setTimeout(() => {
				target.src = generatedImages[index] + '&retry=' + Date.now();
			}, 1000);
		} else {
			errorMessage = `이미지 ${index + 1} 로드에 실패했습니다. URL을 확인해주세요.`;
		}
	}

	// 이미지가 성공적으로 로드되었을 때
	function handleImageLoad(event: Event) {
		const target = event.target as HTMLImageElement;
		target.dataset.retryCount = '0'; // 재시도 카운트 초기화
		console.log('이미지 로드 성공:', target.src);
	}
</script>

<section class="flex min-h-screen items-center justify-center bg-neutral-900 p-4 py-8 sm:p-6">
	<div
		class="w-full max-w-sm rounded-xl bg-teal-500 p-4 shadow-lg outline outline-black/5 sm:max-w-md sm:rounded-2xl sm:p-6 md:max-w-2xl lg:max-w-4xl xl:max-w-6xl"
	>
		<!-- 상단 장식 및 헤더 -->
		<div class="mb-3 flex items-center justify-between">
			<button
				on:click={goHome}
				class="rounded-md bg-teal-700 px-3 py-1.5 text-xs font-medium text-white shadow-md transition-colors hover:bg-teal-800 sm:rounded-lg sm:px-4 sm:py-2 sm:text-sm md:text-base"
			>
				← 돌아가기
			</button>
			<div class="flex gap-1 sm:gap-2">
				<i
					class="material-symbols-rounded text-2xl opacity-20 sm:text-3xl md:text-4xl"
					style="color:black;"
				>
					image
				</i>
				<i
					class="material-symbols-rounded text-2xl opacity-20 sm:text-3xl md:text-4xl"
					style="color:black;"
				>
					photo_library
				</i>
			</div>
			<div class="w-16 sm:w-20 md:w-24"></div>
		</div>

		<!-- 메인 타이틀 섹션 -->
		<div class="mb-4 rounded-lg bg-teal-600 p-2 text-neutral-950 sm:mb-6 sm:rounded-xl sm:p-3">
			<div class="rounded-md bg-teal-200 p-3 sm:rounded-lg sm:p-4">
				<h3 class="text-xl font-semibold opacity-80 sm:text-2xl md:text-3xl">이미지 미리보기</h3>
				<p
					class="mt-2 text-sm leading-relaxed font-semibold opacity-60 sm:mt-3 sm:text-base md:text-lg"
				>
					생성된 이미지를 확인하고 다운로드하세요
				</p>
			</div>
		</div>

		{#if isGenerating}
			<div
				class="mb-3 rounded-lg bg-yellow-400 p-3 text-center shadow-md sm:mb-4 sm:rounded-xl sm:p-4"
			>
				<p class="text-sm font-semibold text-neutral-900 sm:text-base">이미지 생성 중...</p>
				<div class="mt-2 flex justify-center sm:mt-3">
					<div
						class="h-6 w-6 animate-spin rounded-full border-4 border-neutral-900 border-t-transparent sm:h-8 sm:w-8"
					></div>
				</div>
			</div>
		{/if}

		{#if errorMessage}
			<div
				class="mb-3 rounded-lg bg-red-500 p-3 text-center shadow-md sm:mb-4 sm:rounded-xl sm:p-4"
			>
				<p class="text-sm font-semibold text-white sm:text-base">{errorMessage}</p>
				<button
					on:click={() => {
						errorMessage = '';
						window.location.reload();
					}}
					class="mt-2 rounded-md bg-white px-3 py-1.5 text-xs font-medium text-red-600 shadow-sm transition-colors hover:bg-red-50 sm:mt-3 sm:rounded-lg sm:px-4 sm:py-2 sm:text-sm"
				>
					🔄 다시 시도
				</button>
			</div>
		{/if}

		{#if generatedImages.length > 0}
			<!-- Main Image Display -->
			<div class="mb-3 rounded-lg bg-teal-600 p-2 sm:mb-4 sm:rounded-xl sm:p-3">
				<div class="rounded-md bg-white p-3 sm:rounded-lg sm:p-4">
					<div class="relative">
						<img
							src={generatedImages[currentIndex]}
							alt={`생성된 이미지 ${currentIndex + 1}`}
							class="mx-auto max-h-[350px] w-auto rounded-md object-contain sm:max-h-[450px] md:max-h-[550px]"
							on:error={(e) => handleImageError(e, currentIndex)}
							on:load={handleImageLoad}
							crossorigin="anonymous"
						/>
						<button
							on:click={() => downloadImage(generatedImages[currentIndex], currentIndex)}
							class="absolute right-2 bottom-2 rounded-md bg-purple-600 px-3 py-1.5 text-xs font-medium text-white shadow-md transition-colors hover:bg-purple-700 sm:right-3 sm:bottom-3 sm:rounded-lg sm:px-4 sm:py-2 sm:text-sm md:text-base"
						>
							💾 다운로드
						</button>
					</div>
					<div class="mt-3 text-center sm:mt-4">
						<p class="text-sm font-semibold text-neutral-900 sm:text-base md:text-lg">
							이미지 {currentIndex + 1} / {generatedImages.length}
						</p>
						<p class="mt-1 px-2 text-xs break-all text-neutral-600 sm:mt-2 sm:text-sm">
							URL: {generatedImages[currentIndex]}
						</p>
					</div>
				</div>
			</div>

			<!-- Thumbnail Grid -->
			{#if generatedImages.length > 1}
				<div class="rounded-lg bg-teal-600 p-2 sm:rounded-xl sm:p-3">
					<div class="rounded-md bg-teal-100 p-2.5 sm:rounded-lg sm:p-3">
						<h2 class="mb-2 text-base font-semibold text-neutral-900 sm:mb-3 sm:text-lg">
							모든 이미지
						</h2>
						<div
							class="grid grid-cols-2 gap-2 sm:grid-cols-3 sm:gap-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6"
						>
							{#each generatedImages as url, i}
								<button
									on:click={() => selectImage(i)}
									class="group relative overflow-hidden rounded-md border-2 transition-all {i ===
									currentIndex
										? 'border-amber-600 ring-2 ring-amber-500'
										: 'border-teal-300 hover:border-amber-400'}"
								>
									<img
										src={url}
										alt={`썸네일 ${i + 1}`}
										class="h-24 w-full object-cover transition-transform group-hover:scale-110 sm:h-28 md:h-32"
										on:error={(e) => handleImageError(e, i)}
										on:load={handleImageLoad}
										crossorigin="anonymous"
									/>
									<div
										class="absolute inset-0 flex items-center justify-center bg-black/50 opacity-0 transition-opacity group-hover:opacity-100"
									>
										<span class="text-xs font-semibold text-white sm:text-sm">보기</span>
									</div>
								</button>
							{/each}
						</div>
					</div>
				</div>
			{/if}
		{:else if !isGenerating}
			<div class="rounded-lg bg-teal-600 p-3 sm:rounded-xl sm:p-4">
				<div class="rounded-md bg-teal-100 p-6 text-center sm:rounded-lg sm:p-8">
					<p class="text-base font-semibold text-neutral-900 sm:text-lg md:text-xl">
						생성된 이미지가 없습니다.
					</p>
					<button
						on:click={goHome}
						class="mt-3 -translate-y-1 rounded-md bg-amber-600 px-4 py-2.5 text-sm font-medium text-white shadow-[0_4px_0_0_theme('colors.amber.800')] transition-all duration-150 hover:translate-y-0 hover:shadow-none sm:mt-4
						sm:-translate-y-1.5 sm:rounded-lg
						sm:px-6 sm:py-3 sm:text-base sm:shadow-[0_6px_0_0_theme('colors.amber.800')]"
					>
						🏠 메인으로 이동
					</button>
				</div>
			</div>
		{/if}

		<!-- 하단 장식 -->
		<div class="mt-6 flex justify-center sm:mt-8">
			<i
				class="material-symbols-rounded text-2xl opacity-20 sm:text-3xl md:text-4xl"
				style="color:black;"
			>
				photo_camera
			</i>
		</div>
	</div>
</section>
