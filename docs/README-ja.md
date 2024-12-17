# chill

Calculator of Heat Iterative Linear Logic

## 思想
Configurationはpythonで記述し, 実行はRustで高速に実行する熱計算フレームワーク
結果の評価, 可視化もpythonで実施する.
Node-Edge間の関係を記載し, 単純なEdgeのloopのみで非定常状態の計算を実行する.

## インストール
前提として, PythonとRustのインストールが必要.
[rust official page](https://www.rust-lang.org/tools/install).

以上の準備ができていれば, 以下のコマンドを実行するだけで良い.


```
python -m pip install git+https://github.com/mzks/chill
```

## 使用法

### 基本的な使い方
まず, モジュールをインポートして, 計算主体のクラスを作成する.
```
import numpy as np
import matplotlib.pyplot as plt
from chill import Chill
from chill.constants import *

c = Chill()
```

物体を定義する. 物体は全て等温である.
基本的な単位は定義してあるので, `*K` や `*cm3` とすれば, 正しい単位で入力できる.
```
object0 = c.define_object("Al", 500*K, volume=10.*cm3, name='Obj.0')
object1 = c.define_object("Al", 300*K, volume=10.*cm3, name='Obj.1')
```
`define_object` 関数は物質名, 初期温度, 体積を入れれば, 自動的に熱容量を計算する.
熱容量を手でいれたい場合は, 
```
object2 = c.define_node(300*K, 942*J_per_kgK * 3*kg, name='Obj.2')
```
と与える.

物体間の熱的接続を定義する.
`define_thermal_conduction` 関数は接触熱伝達や対流熱伝達を熱抵抗で定義する.
なお, 内部ではSI単位系を使っているので, SI単位系で定義された数値であれば, 単位なしで使ってよい.
```
h_c = 100
area = 10.*cm2
heat_resistance = 1 / (h_c * area)
c.define_thermal_conduction(object0, object1, heat_resistance)
c.define_thermal_conduction(object1, object2, heat_resistance)
```

全てを定義したら,
```
c.setup()
```
でシミュレーションのためのデータを準備する.

`c.dt = 100*ms` などとすると, シミュレーションのStep間隔を変えられる.
この操作は常に有効.

シミュレーションを進めたい時は,
`c.execute(100*s, 1*s)` などと実行する. この例では, 100秒間のシミュレーションを行い,
1秒ごとに全ての物体の温度データを保存する.

結果の解析は

```
c.plot_top_temperature_changes(3)
```
とすると, 顕著な温度差があった物体についてプロットがかける.
物体の名前を使って,
```
plot_node_temperature_by_names(['Obj.0', 'Obj.2'])
```
などと, 必要なものを選んでプロットを作成することも可能.

### 機能詳細

輻射は `c.define_thermal_radiation(node0, node1, rad_const)` で定義.
node0とnode1の温度の4乗の差に比例して温度変化させる. 
`rad_const` はその時の比例定数で, 典型的に `E_G * epsilon * area * sigma` になる.


熱浴などの無限大の熱容量を持った物体は以下で定義する.
```
ambient = c.define_node(temperature=300, capacity=np.inf, name='ambient')
```

ヒーター/クーラーなどの, 一定の熱量を常に物体に与え続ける設定は以下の関数で作る.
```
define_heater(target_node, heat_input)
```

### パフォーマンス評価
これから.
