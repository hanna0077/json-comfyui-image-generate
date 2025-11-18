<script lang="ts">
	import { onMount } from 'svelte';
	import { openAIService } from '$lib/services/openai.service';
	import { workflowService } from '$lib/services/workflow.service';
	import type { EventData } from '$lib/types';
	import { downloadJSON } from '$lib/utils/downloadJSON.utils';
	import { goto } from '$app/navigation';

	let category = 'forest exploration';
	let eventCount = 5;
	let isGenerating = false;
	let generatedEvents: EventData[] = [];
	let errorMessage = '';
	let jsonPreview = '';
	let isOpenAIAvailable = false;
	let workflowList: string[] = [];
	let selectedWorkflow = '';
	let subfolder = '';
	let workflowLoadError = '';
	let manualWorkflowInput = '';
	let useManualWorkflow = false;

	onMount(async () => {
		// OpenAI는 서버에서 관리하므로 클라이언트 초기화는 단순화
		openAIService.initialize();
		isOpenAIAvailable = openAIService.isInitialized();

		// 워크플로우 목록 가져오기
		try {
			workflowList = await workflowService.getWorkflowList();
			if (workflowList.length > 0) {
				selectedWorkflow = workflowList[0];
			} else {
				workflowLoadError = '사용 가능한 워크플로우가 없습니다.';
				useManualWorkflow = true;
			}
		} catch (error) {
			console.error('워크플로우 목록 로드 실패:', error);
			workflowLoadError =
				error instanceof Error ? error.message : '워크플로우 목록을 불러올 수 없습니다.';
			useManualWorkflow = true;
		}
	});

	// 샘플 JSON 생성 함수
	function generateSampleJSON() {
		const sampleTemplates = [
			{
				tags: 'forest, ancient ruins, mystery, stone pillars, twilight',
				background_image:
					'Ancient stone pillars covered in ivy stand in a clearing. Twilight filters through the canopy, creating an ethereal atmosphere. Mysterious symbols are carved into weathered stones.'
			},
			{
				tags: 'forest, river crossing, wooden bridge, mist, morning',
				background_image:
					'A worn wooden bridge spans a crystal-clear forest stream. Morning mist rises from the water, and colorful fish can be seen swimming beneath the surface.'
			},
			{
				tags: 'forest, abandoned camp, campfire, supplies, dusk',
				background_image:
					'An abandoned campsite with a smoldering fire pit. Scattered supplies and a worn backpack suggest recent departure. The setting sun casts long shadows through the trees.'
			},
			{
				tags: 'forest, giant tree, hollow trunk, shelter, glowing mushrooms',
				background_image:
					'A massive ancient tree with a hollow trunk large enough to serve as shelter. Bioluminescent mushrooms grow along the interior walls, casting a soft blue glow.'
			},
			{
				tags: 'forest, wildlife, deer herd, meadow, peaceful',
				background_image:
					'A tranquil meadow where a herd of deer graze peacefully. Wildflowers bloom in abundance, and butterflies dance in the warm afternoon sunlight.'
			},
			{
				tags: 'forest, dark cave entrance, vines, ominous, shadows',
				background_image:
					'A foreboding cave entrance partially concealed by hanging vines. Strange sounds echo from within, and peculiar claw marks are visible on the surrounding rocks.'
			},
			{
				tags: 'forest, treehouse ruins, rope ladder, overgrown, abandoned',
				background_image:
					'The remains of an old treehouse high in the canopy. A frayed rope ladder dangles below, and nature has begun reclaiming the structure with moss and vines.'
			},
			{
				tags: 'forest, waterfall, rainbow, pool, serene',
				background_image:
					"A majestic waterfall cascades into a clear pool below. Sunlight creates a rainbow in the mist, and smooth stones line the water's edge."
			}
		];

		const sampleEvents: EventData[] = [];

		for (let i = 0; i < eventCount; i++) {
			const template = sampleTemplates[i % sampleTemplates.length];
			sampleEvents.push({
				tags: template.tags,
				background_image: template.background_image
			});
		}

		generatedEvents = sampleEvents;
		const wrappedData = { event: sampleEvents };
		jsonPreview = JSON.stringify(wrappedData, null, 2);
		errorMessage = '';
	}

	async function handleGenerateJSON() {
		isGenerating = true;
		errorMessage = '';
		generatedEvents = [];
		jsonPreview = '';

		try {
			const results: EventData[] = [];

			for (let i = 0; i < eventCount; i++) {
				const result = await openAIService.generateSingleEvent(category);
				if (result) {
					results.push(result);
				}
			}

			generatedEvents = results;
			const wrappedData = { event: results };
			jsonPreview = JSON.stringify(wrappedData, null, 2);
		} catch (error) {
			errorMessage =
				error instanceof Error
					? error.message
					: '생성 중 오류가 발생했습니다. 서버를 확인해주세요.';
			console.error(error);
		} finally {
			isGenerating = false;
		}
	}

	function handleDownload() {
		if (generatedEvents.length > 0) {
			const wrappedData = { event: generatedEvents };
			downloadJSON(wrappedData, 'generated_events.json');
		}
	}

	function handleUseForImageGeneration() {
		errorMessage = '';

		if (generatedEvents.length === 0) {
			errorMessage = '먼저 JSON을 생성해주세요.';
			return;
		}

		// 워크플로우 결정: 수동 입력 또는 선택된 워크플로우
		const workflowToUse = useManualWorkflow ? manualWorkflowInput.trim() : selectedWorkflow;

		if (!workflowToUse) {
			errorMessage = '워크플로우를 입력하거나 선택해주세요.';
			return;
		}

		const wrappedData = { event: generatedEvents };
		const jsonString = JSON.stringify(wrappedData, null, 2);

		// localStorage에 생성 요청 정보 저장
		localStorage.setItem(
			'generationRequest',
			JSON.stringify({
				workflow: workflowToUse,
				prompt: jsonString,
				subfolder: subfolder
			})
		);

		goto('/preview');
	}
</script>

<main class="min-h-screen flex items-center justify-center p-4 sm:p-6 py-8">
	<div
		class="w-full max-w-sm sm:max-w-md md:max-w-lg lg:max-w-2xl xl:max-w-4xl rounded-xl sm:rounded-2xl bg-teal-500 p-4 sm:p-6 shadow-lg outline outline-black/5"
	>
		<div class="mb-4 sm:mb-6 rounded-lg sm:rounded-xl bg-teal-600 p-2 sm:p-3 text-neutral-950">
			<div class="rounded-md sm:rounded-lg bg-teal-200 p-3 sm:p-4">
				<h3 class="text-xl sm:text-2xl md:text-3xl font-semibold opacity-80">AI JSON 생성기</h3>
				<p class="mt-2 sm:mt-3 text-sm sm:text-base md:text-lg font-semibold leading-relaxed opacity-60">
					OpenAI를 활용하여 게임 이벤트 JSON을 자동으로 생성합니다
				</p>
			</div>
		</div>

		<div class="space-y-3 sm:space-y-4">
			<div class="flex flex-col sm:flex-row gap-3 sm:gap-4 md:gap-6">
				<label class="block w-full text-sm sm:text-base font-semibold">
					카테고리 (주제)
					<input
						bind:value={category}
						type="text"
						placeholder="예: forest exploration, dungeon adventure"
						class="mt-1.5 sm:mt-2 w-full rounded-md border-2 border-teal-100 bg-teal-100 p-3 sm:p-2.5 text-base sm:text-base"
						disabled={isGenerating}
					/>
				</label>

				<label class="block w-full text-sm sm:text-base font-semibold">
					생성할 이벤트 개수
					<select
						bind:value={eventCount}
						class="mt-1.5 sm:mt-2 w-full rounded-md border-2 border-teal-100 bg-teal-100 p-3 sm:p-2.5 text-base sm:text-base"
						disabled={isGenerating}
					>
						<option value={1}>1개</option>
						<option value={5}>5개</option>
						<option value={10}>10개</option>
						<option value={20}>20개</option>
					</select>
				</label>
			</div>

			{#if !isOpenAIAvailable}
				<div class="rounded-md sm:rounded-lg border border-yellow-400 bg-yellow-100 p-2.5 sm:p-3">
					<p class="text-xs sm:text-sm text-yellow-800 leading-relaxed">
						⚠️ OpenAI 서비스를 사용할 수 없습니다. <br />
						서버(api 폴더)의 <code class="bg-yellow-200 px-1 rounded text-xs">`.env`</code> 파일에
						<code class="bg-yellow-200 px-1 rounded text-xs">OPENAI_API_KEY</code>를 설정해주세요.
					</p>
				</div>
			{/if}

			<div class="grid grid-cols-1 gap-2 sm:gap-3 sm:grid-cols-2">
				<button
					on:click={generateSampleJSON}
					disabled={isGenerating}
					class="rounded-md sm:rounded-lg bg-blue-600 px-4 py-2.5 sm:px-6 sm:py-3 text-sm sm:text-base font-medium text-white shadow-md transition-all duration-150 hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
				>
					📝 샘플 JSON 생성 (테스트용)
				</button>

				<button
					on:click={handleGenerateJSON}
					disabled={isGenerating || !isOpenAIAvailable}
					class="rounded-md sm:rounded-lg bg-amber-600 px-4 py-2.5 sm:px-6 sm:py-3 text-sm sm:text-base font-medium text-white shadow-md transition-all duration-150 hover:bg-amber-700 disabled:cursor-not-allowed disabled:opacity-50"
				>
					{isGenerating ? '🔄 AI JSON 생성 중...' : '✨ AI JSON 생성'}
				</button>
			</div>

			{#if errorMessage}
				<div class="rounded-md sm:rounded-lg bg-red-500 p-2.5 sm:p-3 text-white">
					<p class="text-sm sm:text-base">{errorMessage}</p>
				</div>
			{/if}

			{#if jsonPreview}
				<div class="rounded-lg sm:rounded-xl bg-teal-600 p-2 sm:p-3">
					<div class="rounded-md sm:rounded-lg bg-teal-100 p-2.5 sm:p-3">
						<h4 class="mb-2 text-sm sm:text-base font-semibold">생성된 JSON</h4>
						<pre class="max-h-64 sm:max-h-96 overflow-auto rounded bg-white p-2 sm:p-3 text-xs sm:text-sm">{jsonPreview}</pre>
					</div>
				</div>

				<!-- 이미지 생성 설정 -->
				<div class="rounded-lg sm:rounded-xl bg-teal-600 p-2 sm:p-3">
					<div class="rounded-md sm:rounded-lg bg-teal-100 p-2.5 sm:p-3">
						<h4 class="mb-2 sm:mb-3 text-sm sm:text-base font-semibold">이미지 생성 설정</h4>

						<div class="space-y-2.5 sm:space-y-3">
							<div>
								<label class="mb-1.5 sm:mb-2 block text-xs sm:text-sm font-medium"> 워크플로우 (필수) </label>

								{#if workflowLoadError}
									<div class="mb-2 rounded border border-yellow-400 bg-yellow-100 p-2">
										<p class="text-xs text-yellow-800">⚠️ {workflowLoadError}</p>
										<p class="mt-1 text-xs text-yellow-700">
											아래에 워크플로우 파일명을 직접 입력해주세요.
										</p>
									</div>
								{/if}

								<!-- 워크플로우 선택/입력 토글 -->
								{#if workflowList.length > 0}
									<div class="mb-1.5 sm:mb-2 flex items-center gap-2 sm:gap-3">
										<label class="flex items-center gap-1 text-xs sm:text-sm">
											<input
												type="radio"
												bind:group={useManualWorkflow}
												value={false}
												class="h-3 w-3 sm:h-4 sm:w-4"
											/>
											<span>목록에서 선택</span>
										</label>
										<label class="flex items-center gap-1 text-xs sm:text-sm">
											<input
												type="radio"
												bind:group={useManualWorkflow}
												value={true}
												class="h-3 w-3 sm:h-4 sm:w-4"
											/>
											<span>직접 입력</span>
										</label>
									</div>
								{/if}

								{#if !useManualWorkflow && workflowList.length > 0}
									<select
										bind:value={selectedWorkflow}
										class="w-full rounded-md border-2 border-gray-300 bg-white p-3 sm:p-2.5 text-base sm:text-base"
									>
										{#each workflowList as workflow}
											<option value={workflow}>{workflow}</option>
										{/each}
									</select>
								{:else}
									<input
										bind:value={manualWorkflowInput}
										type="text"
										placeholder="예: workflow.json 또는 dungeon_background.json"
										class="w-full rounded-md border-2 border-gray-300 bg-white p-3 sm:p-2.5 text-base sm:text-base"
									/>
									<p class="mt-1 text-xs sm:text-sm text-gray-600">
										api/workflows 폴더에 있는 워크플로우 파일명을 입력하세요
									</p>
								{/if}
							</div>

							<div>
								<label class="mb-1.5 sm:mb-2 block text-xs sm:text-sm font-medium">
									이미지 저장 폴더 (선택)
									<input
										bind:value={subfolder}
										type="text"
										placeholder="예: forest_images"
										class="mt-1.5 sm:mt-2 w-full rounded-md border-2 border-gray-300 bg-white p-3 sm:p-2.5 text-base sm:text-base"
									/>
								</label>
							</div>
						</div>
					</div>
				</div>

				<div class="flex flex-col sm:flex-row gap-2 sm:gap-3">
					<button
						on:click={handleDownload}
						class="flex-1 rounded-md sm:rounded-lg bg-green-600 px-4 py-2.5 sm:py-3 text-sm sm:text-base font-medium text-white shadow-md transition-all duration-150 hover:bg-green-700"
					>
						📥 JSON 다운로드
					</button>
					<button
						on:click={handleUseForImageGeneration}
						disabled={useManualWorkflow ? !manualWorkflowInput.trim() : !selectedWorkflow}
						class="flex-1 rounded-md sm:rounded-lg bg-blue-600 px-4 py-2.5 sm:py-3 text-sm sm:text-base font-medium text-white shadow-md transition-all duration-150 hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
					>
						🎨 이미지 생성하기
					</button>
				</div>
			{/if}
		</div>

		<div class="mt-4 sm:mt-6 flex justify-center">
			<button
				on:click={() => goto('/')}
				class="rounded-md sm:rounded-lg bg-teal-700 px-4 py-2 sm:px-6 sm:py-2.5 text-sm sm:text-base font-medium text-white shadow-md transition-all duration-150 hover:bg-teal-800"
			>
				← 홈으로 돌아가기
			</button>
		</div>
	</div>
</main>
