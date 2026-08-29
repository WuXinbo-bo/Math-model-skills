# 常用建模方法参考表

| 问题类别 | 常用方法 | Python 库 |

|----------|----------|-----------|

| 线性规划 | 单纯形法、内点法 | scipy.optimize.linprog, PuLP, Gurobi |

| 整数规划 | 分支定界、割平面 | PuLP, Gurobi, OR-Tools |

| 非线性优化 | 梯度下降、遗传算法 | scipy.optimize.minimize, DEAP |

| 多目标优化 | NSGA-II、加权法 | pymoo, platypus |

| 回归分析 | OLS、岭回归、LASSO | sklearn, statsmodels |

| 时间序列 | ARIMA、指数平滑、LSTM | statsmodels, pmdarima, keras |

| 聚类分析 | K-means、DBSCAN、层次聚类 | sklearn |

| 层次分析 | AHP 一致性检验 | 人工实现 / ahpy |

| TOPSIS | 理想解排序 | 人工实现 |

| 灰色预测 | GM(1,1) | 人工实现 |

| 图论 | Dijkstra、Floyd、最大流 | networkx |

| 蒙特卡洛 | 随机模拟 | numpy.random |

| 微分方程 | Euler、Runge-Kutta | scipy.integrate |

| 运动学与动力学 | 状态方程、解析轨迹、数值积分 | scipy.integrate, sympy |

| 几何可见性与遮挡 | 点线面距离、相交判据、计算几何 | numpy, scipy.spatial, shapely |

| 连续时间事件模型 | 粗网格定位、根求解、二分精化、区间集合 | scipy.optimize, portion |

| 仿真优化 | 机理仿真器、代理模型、黑箱约束优化 | scipy.optimize, pymoo |

| 混合离散-连续模型 | 指派/路径/调度与连续控制分解、MINLP | OR-Tools, Pyomo, scipy.optimize |

| 集合覆盖与时间区间 | 区间并集、重叠、边际贡献、最大覆盖 | portion, intervaltree, scipy |

方法表只用于识别数学结构。库和算法必须根据可微性、凸性、变量类型、维度、精度与计算预算选择，不能反向用算法名称定义模型。

