<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { workflowService } from '$lib/services/workflow.service';

	let workflowList: string[] = [];

	onMount(() => {
		async function getWorkflowList() {
			workflowList = await workflowService.getWorkflowList();
		}
		getWorkflowList();
	});

	function handleNextPage(workflow: string) {
		goto(`/prompt?workflow=${encodeURIComponent(workflow)}`);
	}
</script>

<main class="min-h-screen flex items-center justify-center p-4 sm:p-6 py-8">
	<div
		class="w-full max-w-sm sm:max-w-md md:max-w-lg lg:max-w-2xl xl:max-w-4xl rounded-xl sm:rounded-2xl bg-teal-500 p-4 sm:p-6 shadow-lg outline outline-black/5"
	>
		<!-- 상단 장식 -->
		<div class="mb-3 flex justify-between items-center">
			<i class="material-symbols-rounded text-2xl sm:text-3xl md:text-4xl opacity-20" style="color:black;">
				add_circle
			</i>
			<div class="flex gap-1 sm:gap-2">
				<i
					class="material-symbols-rounded text-2xl sm:text-3xl md:text-4xl opacity-20"
					style="color:black; transform: scaleX(-1);"
				>
					menu_open
				</i>
				<span class="material-symbols-rounded text-2xl sm:text-3xl md:text-4xl opacity-20" style="color:black;">
					menu
				</span>
				<i class="material-symbols-rounded text-2xl sm:text-3xl md:text-4xl opacity-20" style="color:black;">
					menu_open
				</i>
			</div>
			<i class="material-symbols-rounded text-2xl sm:text-3xl md:text-4xl opacity-20" style="color:black;">
				add_circle
			</i>
		</div>

		<!-- 메인 타이틀 섹션 -->
		<div class="rounded-lg sm:rounded-xl bg-teal-600 p-2 sm:p-3 text-neutral-950">
			<div class="h-full w-full rounded-md sm:rounded-lg bg-teal-200 p-3 sm:p-4 md:p-5">
				<h3 class="text-xl sm:text-2xl md:text-3xl font-semibold opacity-80">AI 이미지 생성 도구</h3>
				<p class="mt-2 sm:mt-3 text-sm sm:text-base md:text-lg leading-relaxed font-semibold opacity-60">
					AI로 JSON을 생성하거나, 워크플로우를 선택하여 이미지를 생성하세요
				</p>
			</div>
		</div>

		<!-- JSON 생성 버튼 -->
		<div class="mt-4 sm:mt-6 mb-3 sm:mb-4">
			<button
				on:click={() => goto('/generate')}
				class="-translate-y-1.5 sm:-translate-y-2 w-full rounded-md sm:rounded-lg bg-purple-600 px-4 py-2.5 sm:px-6 sm:py-3 text-sm sm:text-base md:text-lg font-medium text-white
				shadow-[0_6px_0_0_theme('colors.purple.800')] sm:shadow-[0_8px_0_0_theme('colors.purple.800')]
				transition-all duration-150 ease-in-out
				hover:translate-y-0
				hover:shadow-none active:translate-y-0 active:bg-purple-700
				active:text-white/70 active:shadow-none"
			>
				🤖 AI로 JSON 생성하기
			</button>
		</div>

		<!-- 워크플로우 목록 -->
		<div class="mt-4 sm:mt-6">
			{#if workflowList.length > 0}
				<div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 sm:gap-4">
					{#each workflowList as workflow}
						<div class="flex flex-col h-full">
							<div class="rounded-md sm:rounded-lg bg-teal-600 p-2 sm:p-3 pb-4 sm:pb-5 h-full flex items-stretch">
								<button
									value={workflow}
									on:click={() => handleNextPage(workflow)}
									class="-translate-y-1.5 sm:-translate-y-2 w-full min-h-[48px] rounded-md sm:rounded-lg bg-amber-600 px-4 py-2.5 sm:px-6 sm:py-3 text-sm sm:text-base md:text-lg font-medium text-white
									shadow-[0_6px_0_0_theme('colors.amber.800')] sm:shadow-[0_8px_0_0_theme('colors.amber.800')]
									transition-all duration-150 ease-in-out
									hover:translate-y-0
									hover:shadow-none active:translate-y-0 active:bg-amber-700
									active:text-white/70 active:shadow-none break-words hyphens-auto"
									style="word-break: break-word;"
								>
									{workflow}
								</button>
							</div>
						</div>
					{/each}
				</div>
			{:else}
				<p class="text-center text-sm sm:text-base text-neutral-900 opacity-60 py-4">워크플로를 불러오는 중...</p>
			{/if}
		</div>

		<!-- 하단 장식 -->
		<div class="mt-6 sm:mt-8 flex justify-between items-center">
			<i class="material-symbols-rounded text-2xl sm:text-3xl md:text-4xl opacity-20" style="color:black;">
				add_circle
			</i>
			<i class="material-symbols-rounded text-2xl sm:text-3xl md:text-4xl opacity-20" style="color:black;">
				menu
			</i>
			<i class="material-symbols-rounded text-2xl sm:text-3xl md:text-4xl opacity-20" style="color:black;">
				add_circle
			</i>
		</div>
	</div>
</main>
