nums = [3, 2, 4]
target = 6


for i in range(0, len(nums) - 1):
	for j in range(0, len(nums)):
		if target == nums[i] + nums[j]:
			print(i, j)
