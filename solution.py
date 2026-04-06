class Solution:
    def twoSum(self, nums: List[int], target: int) -> List[int]:
        # Our hash table that stores at which index the number is at
        numToIndex = {}

        # 1. Iterate over every number in the array
        for i in range(len(nums)):
            # 2. Calculate the complement that would sum to our target
            complement = target - nums[i]

            # 3. Check if that complement is in our hash table
            if complement in numToIndex:
                return numToIndex[complement], i

            # 4. Add the current number to our hash table
            numToIndex[nums[i]] = i
