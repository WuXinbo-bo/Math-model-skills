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

