# TODO List


## Step

1. 在 `global.json` 中加入 `index2phase` 的信息
2. 在 `global.json` 中加入 `phaseInfo` 信息，将 traffic phase 和 image 和 lane index 的关系对应起来


1. 处理 `global.json` 文件，将 can perform action 部分修改位置

---


注意，关于 index 初始位置：
1. Phase 从 0 开始
2. image index 从 0 开始
3. lane index 从 1 开始

## 原始 VQA 生成

- [x] incoming 和 outgoing 的 threshold 数值可以设置不一样
- [x] bev to directions, directions to bev, 这里修改为不相关的是
- [x] 单图问题的时候，生成特定车道上有多少车辆
- [x] 时序问题的时候，出现两位数和三位数 timestep 混合在一起
- [] 统计车辆的时候去除 other other_accidents

## Sample VQA 需要加上

- [x] 加入特定车道有多少车辆的任务
- [ ] time order 任务, 尽量选择有车的场景
- [ ] 多图任务中，哪个图片车辆最多，检查为什么选项都是 A

## HTML 可视化

- [x] 生成 4 选 1 的时候格式不对，question 是单独的图，下面是选项


5. 完成一个十字路口的测试