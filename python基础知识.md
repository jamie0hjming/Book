[TOC]

### 一、Python中的数据类型

> 计算机顾明思议就是可以做数学运算的机器,因此计算机理所当然的可以处理各种数据,但是计算机能处理的远远不止数值,还有文本,图形,音频,视频网页等各种数据, 不同数据需要定义不同的数据类型
>
> Number【数字：整型int，浮点型[小数]float，复数类型complex】
>
> String【字符串】
>
> Boolean【布尔类型】 True真（1）， Flase假（0）
>
> None【空值】
>
> list【列表】
>
> tuple【元组】 不可改变的列表
>
> dict【字典】
>
> set【集合】
>
> bytes【字节】

### 1.Number

#### 1.1分类

##### 1.1.1 整数

> 可以处理Python中任意大小的整型
>
> 代码演示：
>
> ```python
> num1 = 10
> num2 = num1
> print(num1,num2)
>
> ```

##### 1.1.2浮点数

> 由整数部分和小数部分组成
>
> 注意：浮点数在计算机中运算的时候可能会出现四舍五入

#####  1.1.3复数

> 由实数部分和虚数部分组成
>
> 表示形式：a + bj或者complex(a,b)

#### 1.2 数字类型转换

> int(x):将x转换为整数
>
> float(x)：将x转换为一个浮点数
>
> 代码演示：
>
> ```python
> print(int(1.9))   #1   取整
> print(float(1))   #1.0
> print(int("123"))   #123
> print(float("12.3")) #12.3
>
> #使用int或者float进行转换的时候，如果字符串中出现特殊符号，则转换失败
> #print(int("abc123"))   #ValueError: invalid literal for int() with base 10: 'abc123'
>
> print(int("+123"))   #123，当做数学上的正负号
> #print(int("12+3"))   #ValueError: invalid literal for int() with base 10: '12+3'
> print(int("-123"))  #-123
> #print(int("12-3"))  #ValueError: invalid literal for int() with base 10: '12-3'
>
> ```

### 2. string 字符串

#### 2.1.概述

> 由多个字母，数字，特殊字符组成的有限序列
>
> 在Python中，使用单引号或者双引号都可以表示字符串
>
> 注意:没有单符号的数据类型
>
> 'a' "a"

#### 2.2.创建字符串

> 代码演示：
>
> ```
> str1 = "hello"
>
> str2 = "abc1234"
>
> str3 = "***fhhg%%%"
>
> str4 = "中文"
>
> ```

#### 2.3.字符串运算

> 代码演示：
>
> ```
> #1.+   字符串连接
> s1 = "welcome"
> s2 = " to China"
> print(s1 + s2)
>
> #注意：在Python中，使用+。只能是字符串和字符串之间。和其他数据类型使用的话不支持
> #print("abc" + 10)
> #print("123" + 1)
> #print(1 + "12" + 12)
> #print("hello" + True)
>
> #2. *   字符串重复
> s3 = "good"
> print(s3 * 3)
>
> #3.获取字符串中的某个字符
> """
> 类似于列表和元组的使用，通过索引来获取指定位置的字符
> 注意索引的取值范围【0~长度 - 1】，同样会出现索引越界
> 访问方式：字符串名称[索引]
> """
> s4 = "abcdef"
> print(s4[1])
> #print(s4[10])  #IndexError: string index out of range
>
> #获取字符串的长度：len()
> #遍历字符串,和list，tuple的用法完全相同
> for element in s4:
>     print(element)
> for index in range(0,len(s4)):
>     print(s4[index])
> for index,str in enumerate(s4):
>     print(index,str)
>
> #4.截取字符串【切片】
> str1 = "hello world"
> #指定区间
> print(str1[3:7])
> #从指定位置到结尾，包含指定位置
> print(str1[3:])
> #从开头到指定位置，但是不包含指定位置
> print(str1[:7])
>
> str2 = "abc123456"
> print(str2[2:5]) #c12
> print(str2[2:])  #c123456
> print(str2[2::2])  #c246
> print(str2[::2])   #ac246
> print(str2[::-1])  #654321cba   倒序
> print(str2[-3:-1])  #45   -1表示最后一个字符
>
> #5.判断一个子字符串是否在原字符串中
> #in  not in
> str3 = "today is a good day"
> print("good"  in str3)
> print("good1"  not in str3)
>
> ```

#### 2.4.格式化输出

> 通过%来改变后面字母或者数字的含义，%被称为占位符
>
>  %d 整数
>
>  %f 浮点型，特点：可以指定小数点后的位数
>
>  %s 字符串
>
> 代码演示：
>
> ```python
> #6.格式化输出
> num = 10
> string1 = "hello"
> print("string1=",string1,"num=",num)
> #注意：变量的书写顺序尽量和前面字符串中出现的顺序保持一致
> print("string1=%s,num=%d"%(string1,num))
>
> f = 12.247
> print("string1=%s,num=%d,f=%f"%(string1,num,f))
> #需求：浮点数保留小数点后两位
> print("string1=%s,num=%d,f=%.2f"%(string1,num,f))    #round(12.247,2)
>
> ```

#### 2.5.常用转义字符

> 通过\来改变后面字母或者特殊字符的含义
>
>  \t 相当于tab键
>
>  \n 相当于enter键
>
>  \b 相当于backspace
>
> 代码演示：
>
> ```python
> #7.转义字符
> string2 = "hello\tworld"
> string21 = "hello   world"
> print(string2)
> print(string21)
>
> #换行：\n    多行注释
> string3 = "hello\nPython"
> string31 = """hello
> python2354623
> """
> print(string3)
> print(string31)
>
> #需求："hello"
> print("\"hello\"")
>
> #C:\Users\Administrator\Desktop\SZ-Python1805\Day6\视频
> print("C:\\Users\\Administrator\\Desktop")
> #注意;如果一个字符串中有多个字符需要转义，则可以在字符串的前面添加r,可以避免对字符串中的每个特殊字符进行转义
> print(r"C:\Users\Administrator\Desktop")
>
> ```

#### 2.6.常用功能

##### 2.6.1获取长度和次数

> 代码演示：
>
> ```python
> #1.计算字符串长度  len
> #类似于list和tuple的中获取长度的用法
> str1 = "hfufhja"
> l = len(str1)
> print(l)
>
> #2,计算某个字符或者子字符串在原字符串中出现的次数   count
> str2 = "this is a good day good day"
> #count(str,[start,end])
> #在整个字符串中进行查找
> print(str2.count("day"))
> #在指定区间内进行查找
> print(str2.count("day",3,10))
>
> ```

##### 2.6.2大小写转换

> 代码演示：
>
> ```python
> #注意：使用字符串中的功能，一般情况下，都是生成一个新的字符串，原字符串没有发生任何变化
> #3.大小写字母转换
> #lower()   将字符串中的大写字母转换为小写
> str31 = "Today Is a Good day"
> astr31 = str31.lower()
> print(astr31)
>
> #uppper()   将字符串中小写字母转换为大写
> str32 = "Today Is a Good day"
> astr32 = str2.upper()
> print(astr32)
>
> #swapcase()     将字符串中小写字母转换为大写，大写字母转换为小写
> str33 = "Today Is a Good day"
> astr33 = str33.swapcase()
> print(astr33)
>
> #capitalize()   将一句英文中首单词的首字母转化为大写，其他小写
> str34 = "today Is a Good day"
> astr34 = str34.capitalize()
> print(astr34)
>
> #title()       将一句英文中每个单词的首字母大写
> str35 = "today is a good day"
> astr35 = str35.title()
> print(astr35)
>
> ```

##### 2.6.3整数和字符串转换

> 代码演示：
>
> ```python
> 4.字符串和数字之间的转换
> #int()     float()      str()
> #eval(str)   将str转换为有效的表达式，参与运算，并返回运算结果
> num1 = eval("123")
> print(num1)
> #print("123")
> print(type(num1))
> print(int("123"))
>
> #eval和int将+和-当做正负号处理
> print(eval("+123"))
> print(int("+123"))
> print(eval("-123"))
> print(int("-123"))
>
> #将12+3字符串转换为了有效的表达式，并运算了结果
> print(eval("12+3"))    #15
> #不成立
> #print(int("12+3"))   #ValueError: invalid literal for int() with base 10: '12+3'
>
> print(eval("12-3"))   #9
> #print(int("12-3"))    #ValueError: invalid literal for int() with base 10: '12-3'
>
> #print(eval("a123"))  #NameError: name 'a123' is not defined
> #print(int("a123"))  #ValueError: invalid literal for int() with base 10: 'a123'
>
> ```

##### 2.6.4填充

> 代码演示：
>
> ```python
> #5.填充【了解】
> #center（width[,fillchar]） 返回一个指定宽度的居中字符串，width是填充之后整个字符串的长度，fillchar为需要填充的字符串，默认使用空格填充
> str1 = "hello"
> print(str1.center(20))
> print(str1.center(10,"*"))
>
> #ljust（width[,fillchar]） 返回一个指定宽度的字符串，将原字符串居左对齐，width是填充之后整个字符串的长度
> print(str1.ljust(40,"%"))
>
> #rjust width[,fillchar]） 返回一个指定宽度的字符串，将原字符串居右对齐，width是填充之后整个字符串的长度
> print(str1.rjust(40,"%"))
>
> #zfill（width） 返回一个指定宽度的字符串,将原字符串居右对齐,剩余的部分使用的数字0填充
> print(str1.zfill(40))
>
> ```

##### 2.6.5查找

> 代码演示：
>
> ```python
> #6.查找【掌握】
> str2 = "abcdefhello123hello"
> #find（str[,start,end]） 从左到右依次检测，str是否在原字符串中，，也可以指定查找的范围
> #特点;得到的子字符串第一次出现的开始字符的下标，如果查找不到则返回-1
> print(str2.find("hello"))    #6
> print(str2.find("e"))
> print(str2.find("yyy"))    #-1
> print(str2.find("e",3,10))
>
> #rfind(str[,start,end]） 类似于find，从右向左进行检测
> print(str2.rfind("hello"))  #14
>
> #index   和find的使用基本相同，唯一的区别在于如果子字符串查找不到，find返回-1，而index则直接报错
> print(str2.index("hello"))
> #print(str2.index("yyy"))   #ValueError: substring not found
>
> #rindex  和rfind的使用基本相同
>
> #max(str)   获取str中最大的字母【在字典中的顺序】
> #"abcdefhello123hello"
> print(max(str2))
>
> str3 = "46732647"
> print(max(str3))
>
> #min（str） 获取str中最小的字母【在字典中的顺序】
>
> ```

##### 2.6.6提取

> 代码演示：
>
> ```python
> #7.提取字符串
> #strip(str)    使用str作为条件提取字符串，除了两头指定的字符串
> str1 = "********today is *********a good day*******"
> print(str1.strip("*"))   #today is *********a good day
>
> #lstrip(str)    提取字符串，除了左边的指定字符串
> str11 = "********today is *********a good day*******"
> print(str11.lstrip("*"))
>
> #rstrip()
> str12 = "********today is *********a good day*******"
> print(str12.rstrip("*"))
>
> ```

##### 2.6.7分割和合并

> 代码演示：
>
> ```python
> #8.分割和合并【掌握：正则表达式】
> #split(str[,num)]   将str作为分隔符切割原字符串，结果为一个列表,如果制定了num，则仅使用num个字符串截取原字符串
> str3 = "today is a good day"
> print(str3.split(" "))   #['today', 'is', 'a', 'good', 'day']
> print(str3.split(" ",2))   #['today', 'is', 'a good day']
>
> #splitlines(flag)   按照换行符【\n，\r,\r\n】分隔，结果为列表
> #flag:False或者不写，则表示忽略换行符；如果True，则表示保留换行符
> str4 = """today
> is
> a
> good
> day
> """
> print(str4.splitlines(True))   #['today', 'is', 'a', 'good', 'day']    ['today\n', 'is\n', 'a\n', 'good\n', 'day\n']
>
> #join(list)    将原字符串作为连接符号，将列表中的元素分别连接起来，结果为字符串，作用和split是相反的
> str5 = "*"
> list1 = ["shangsan","lisi","jack"]
> print(str5.join(list1))
>
> ```

##### 2.6.8替换

> 代码演示：
>
> ```python
> #9.替换
> #replace(old,new[,max])   用new的字符串将old的字符串替换掉.max表示可以替换的最大次数【从左到右】
> str1 = "this is a easy test test test test"
> print(str1.replace("test","exam"))
> print(str1.replace("test","exam",2))
>
> #使用场景：在一定情境下，可以实现字符串的简单加密，加密规则可以自定义
> #maketrans()   创建字符映射的转换表,结果为字典，通过key:value的方式
> #translate(table)
>
> t = str.maketrans("aco","123")
> print(t)   #{97: 49, 99: 50, 111: 51}
>
> str2 = "today is a good day"
> print(str2.translate(t))  #t3d1y is 1 g33d d1y
>
> ```

##### 2.6.9判断

> 代码演示：
>
> ```python
> #10.判断
> #isalpha()   如果字符串中至少包含一个字符并且所有的字符都是字母，才返回True
> print("".isalpha())
> print("abc".isalpha())
> print("abc123".isalpha())   #False
>
> #isalnum   如果字符串中至少包含一个字符并且所有字符都是字母或者数字的时候才返回True
> print("".isalnum())   #False
> print("abc".isalnum())
> print("abc123".isalnum())
> print("123".isalnum())
> print("1abc".isalnum())
> print("1abc￥".isalnum())  #False
>
> #isupper  如果字符串中至少包含一个字符并且出现的字母必须是大写字母才返回True，数字的出现没有影响
> print("".isupper())
> print("aBC".isupper())
> print("123A".isupper())   #True
> print("abc".isupper())
>
> #islower
>
> #istitle   每个单词的首字母必须全部大写才返回True
> print("Good Day".istitle())
> print("good Day".istitle())
>
> #isdigit() 【掌握】 如果字符串中只包含数字，则返回True
> print("abc123".isdigit())
> print("2364".isdigit())
>
> #需求：将用户从控制台输入的字符串转化为整型【全数字】
> str = input()
> if str.isdigit():
>     int(str)
>     print("yes")
>
>
> ```

##### 2.6.10前缀和后缀

> 代码演示：
>
> ```python
> #11.前缀和后缀【掌握】 子字符串是连续的
> #startswith
> str1 = "helloPython"
> print(str1.startswith("hello"))
>
> #endswith
> print(str1.endswith("on"))
> ```

### 3. Boolean（布尔值）

一个布尔类型的变量一般有两个值，True,False

作用：用于分支和循环语句中作为条件判断

代码演示：

```python
#Boolean
b1 = True
b2 = False

#条件表达式或者逻辑表达式结果都是布尔值
print(4 > 5)
print(1 and 0)
```

### 4.None （空值）

Python中的一种特殊的数据类型，使用None表示

区别与0：0是数字类型，None本身就是一种数据类型

代码演示：

```python
#空值
n = None
print(n)   #None
```

### 5.list （列表）

#### 5.1.创建列表

> num = 10
>
> 语法：变量名 = 列表
>
>  列表名称 = [数据1，数据2.。。。。。]
>
> 说明：使用[]表示创建列表
>
>  列表中存储的数据被称为元素
>
>  列表中的元素被从头到尾自动进行了编号，编号从0开始，这个编号被称为索引，角标或者下标
>
>  索引的取值范围：0~元素的个数 - 1【列表的长度 - 1】
>
>  超过索引的范围：列表越界
>
> 代码演示：
>
> ```python
> #语法：列表名【标识符】 = [元素1，元素2.。。。。]
> #1.创建列表
> #1.1创建一个空列表
> list1 = []
> print(list1)
>
> #1.2创建一个带有元素的列表
> list2 = [52,463,6,473,53,65]
> print(list2)
>
> #2.思考问题：列表中能不能存储不同类型的数据？
> list3 = ['abc',10,3.14,True]
> print(list3)
>
> #注意：将需要存储的数据放到列表中，不需要考虑列表的大小，如果数据量很大的情况，在进行存储数据的时候，列表底层自动扩容
>
> ```

#### 5.2.列表元素的访问

> 访问方式：通过索引访问列表中的元素【有序，索引：决定了元素在内存中的位置】

##### 5.2.1获取元素

> 语法：列表名[索引]
>
> 代码演示：
>
> ```python
> #元素的访问
> #创建列表
> list1 = [5,51,6,76,98,3]
>
> #需求：获取索引为3的位置上的元素
> num = list1[3]
> print(num)
> print(list1[3])
>
> ```

##### 5.2.2修改元素

> 语法：列表名[索引] = 值
>
> 注意：列表中存储的是其实是变量，所以可以随时修改值
>
> 代码演示：
>
> ```python
> #需求：将索引为1位置上的元素修改为100
> print(list1[1])
> list1[1] = 100
> print(list1[1])
>
> #问题：超过索引的取值范围，则会出现索引越界的错误
> #解决办法：检查列表索引的取值范围
> #print(list1[6])   #IndexError: list index out of range   索引越界
>
> ```

#### 5.3.列表的基本操作

##### 5.3.1列表元素组合

> 代码演示：
>
> ```python
> #列表组合【合并】
> #使用加号
> list1 = [432,435,6]
> list2 = ["abc","dhfj"]
> list3 = list1 + list2
> print(list3)  #[432, 435, 6, 'abc', 'dhfj']
>
> ```

##### 5.3.2列表元素重复

> 代码演示：
>
> ```python
> #列表元素的重复
> #使用乘号
> list4 = [1,2,3]
> list5 = list4 * 3
> print(list5)  #[1, 2, 3, 1, 2, 3, 1, 2, 3]
>
> ```

##### 5.3.3判断元素是否在列表中

> 代码演示：
>
> ```python
> #判断指定元素是否在指定列表中
> #成员运算符   in  not in
> list6 = [32,43,546,"hello",False]
> print(43 in list6)
> print(43 not in list6)
> print(100 in list6)
> print(100 not in list6)
> """
> 工作原理：使用指定数据在列表中和每个元素进行比对，只要元素内容相等，则说明存在的
> True
> False
> False
> True
> """
>
> ```

##### 5.3.4列表截取【切片】

> 代码演示：
>
> ```python
> #列表的截取
> list7 = [23,34,6,57,6878,3,5,4,76,7]
> print(list7[4])
>
> #使用冒号:
> #截取指定的区间：列表名[开始索引：结束索引],特点：包头不包尾 前闭后开区间
> print(list7[2:6])
>
> #从开头截取到指定索引，特点：不包含指定的索引
> print(list7[0:6])
> print(list7[:6])
>
> #从指定索引截取到结尾
> #注意：因为包头不包尾，所以如果要取到最后一个元素，可以超过索引的范围，不会报错
> print(list7[4:20])
> print(list7[4:])
> ```

### 6.tuple (元组)

创建元组

 创建空元组：tuple1 = ()

 创建有元素的元组：tuple1 = (元素1，元素2，。。。。)

代码演示：

```
#创建空元组：
tuple1 = ()

#创建有元素的元组：
tuple2 = (10,20,30)

#在元组中可以存储不同类型的数据
tuple3 = ("hello",True,100)

#注意：创建只有一个元素的元组
#按照下面的方式书写，表示定义了一个整型的变量，初始值为1
tuple4 = (1)
tuple4 = 1
#为了消除歧义，修改如下：
tuple4 = (1,)

num1 = 10
num2 = (10)
print(num1,num2)
```

### 7.dict (字典)

key-value 构成的容器

#### 7.1 key的特性

> a.字典中的key必须是唯一的
>
> b.字典中的key必须是不可变的

#### 7.2 字典的创建

> 语法：字典名称 = {key1:value1,key2:value2,.......}
>
> 代码演示：
>
> ```python
> #创建空字典
> dict1 = {}
>
> #创建带有键值对的字典
> dict2 = {"zhangsan":96,"lisi":60,"jack":80}
> print(dict2)
> ```

#### 7.3 元素访问

##### 7.3.1 获取

> 语法：字典名[key]
>
> 代码演示：
>
> ```
> #字典中元素的访问
> dict1 = {"zhangsan":96,"lisi":60,"jack":80}
> #1.获取
> #通过key获取对应的value
> score = dict1["lisi"]
> print(score)
>
> #如果key不存在的时候，无法访问
> #print(dict1["tom"])  #KeyError: 'tom'
>
> #虽然key不存在，但是不会报错，返回的是None
> result = dict1.get("tom")
> print(result)
> if result == None:
>     print("key不存在")
> else:
>     print("key是存在的")
>
> ```

##### 7.3.2 添加

> 代码演示：
>
> ```
> #2.修改和添加
> print(dict1)
> #当key不存在的时候，表示添加一对键值对
> dict1["tom"] = 70
> print(dict1)
> #当key存在的时候，表示修改对应的value
> dict1["lisi"] = 88
> print(dict1)
>
> ```

##### 7.3.3 删除

> 代码演示：
>
> ```
> #3.删除
> #注意：删除指定的key，则对应的value也会随着被删除
> dict1.pop("lisi")
> print(dict1)
> ```

#### 7.4.字典的遍历

```
dict1 = {'zhangsan': 96, 'lisi': 88, 'jack': 80, 'tom': 70}

#1.只获取key【掌握】
for key in dict1:
    #通过key获取value
    value = dict1[key]
    print(key,"=",value)
```



### 8.set （集合）

#### 8.1.创建

> set(列表或者元组或者字典)
>
> 代码演示：
>
> ```python
> #注意：set的创建需要借助于list和tuple
>
> #1.通过list创建set
> list1 = [432,5,5,46,65]
> s1 = set(list1)
> print(list1)
> print(s1)
>
> #注意1：set中会自动将重复元素过滤掉
>
> #2.通过tuple创建set
> tuple1 = (235,45,5,656,5)
> s2 = set(tuple1)
> print(tuple1)
> print(s2)
>
> #3.通过dict创建set
> dict1 = {1:"hello",2:"good"}
> s3 = set(dict1)
> print(dict1)   #{1: 'hello', 2: 'good'}
> print(s3)   #{1, 2}
>
> #注意2：set跟dict类似，都使用{}表示，但是与dict之间的区别在于：set中相当于只存储了一组key，没有value
>
> ```

#### 8.2.操作

##### 8.2.1添加

> 代码演示：
>
> ```python
> #1.添加
> #add()   在set的末尾进行追加
> s1 = set([1,2,3,4,5])
> print(s1)
> s1.add(6)
> print(s1)
>
> #注意：如果元素已经存在，则添加失败
> s1.add(3)
> print(s1)
> #print(s1.add(3))
>
> #s1.add([7,8,9])   #TypeError: unhashable type: 'list'  list是可变的，set中的元素不能是list类型
> s1.add((7,8,9))
> #s1.add({1:"a"})  #TypeError: unhashable type: 'dict'  ，dict中的键值对可以改变，set中的元素不能是dict类型
> print(s1)
>
> #update()   插入【末尾添加】，打碎插入【直接将元组，列表中的元素添加到set中，将字符串中的字母作为小的字符串添加到set中】
> s2 = set([1,2,3,4,5])
> print(s2)
> s2.update([6,7,8])
> s2.update((9,10))
> s2.update("good")
> #注意：不能添加整型，因为整型不能使用for循环遍历
> #s2.update(11)   #TypeError: 'int' object is not iterable
> print(s2)
>
> ```

##### 8.2.2删除

> 代码演示：
>
> ```
> #2.删除
> #remove()
> s3 = set([1,2,3,4,5])
> print(s3)
> s3.remove(3)
> print(s3)
>
> ```

##### 8.2.3遍历

> 代码演示：
>
> ```
> #3.set的遍历
> s4 = set([1,2,3,4,5])
> for i in s4:
>     print(i)
>
> #注意：set是没有索引的，所以不能通过s4[2]获取元素，原因：set是无序的
> #print(s4[2])  #TypeError: 'set' object does not support indexing
>
> #注意：获取的是编号和元素值
> for i,num in enumerate(s4):
>     print(i,num)
>
> ```

##### 8.2.4交集和并集

> 代码演示：
>
> ```python
> #4.交集和并集
> s4 = set([1,2,3])
> s5 = set([4,5,3])
>
> #交集：&【按位与】    and
> r1 = s4 & s5
> print(r1)
> print(type(r1))
>
> #并集:|【按位或】   or
> r2 = s4 | s5
> print(r2)
> ```

### 9.bytes （字节）

### 二、运算符和表达式

#### 1.表达式

> 操作数和运算符组成
>
> 1 + 3
>
> 1 / 2
>
> 作用: 表达式可以求值，也可以给变量赋值

#### 2.运算符【掌握】

##### 2.1. 算术运算符

> ```
> +   -    *【乘法】   /【除法】   %【求余，取模】  **【求幂】  //【取整】
>
> ```
>
> 代码演示：
>
> ```
> num1 = 5
> num2 = 3
> print(num1 + num2)
> print(num1 - num2)
> print(num1 * num2)
> print(num1 / num2)  #浮点型：1.6666666666666667    默认精度16位
> print(num1 % num2)  #2
> print(num1 ** num2) #5的3次方
> print(num1 // num2) #获取浮点数的整数部分
>
> #除了+和-之外，其他的算术运算符都是相同的优先级
> #出现优先级，解决办法使用括号
> print(2 ** 5 * 3)
>
> ```

##### 2.2. 赋值运算符

> 简单赋值运算符：= 给一个变量进行赋值
>
> 复合赋值运算符：+= -= %= /= ....... 给一个变量进行赋值，同时给变量进行相应的运算
>
> 代码演示：
>
> ```
> #简单
> num1 = 10
> #注意：在赋值运算符中，先计算等号右边的表达式，然后将计算的结果赋值给等号左边的变量
> num2 = num1 + 10
> print(num2)
>
> #复合
> num3 = 10
> num3 += 100   #等价于num3 = num3 + 100
> print(num3)
>
> ```

##### 2.3. 关系【条件，比较】运算符

> 作用：比较大小，得到结果为布尔值【如果表达式成立，则返回True，如果不成立，则返回False】
>
> ```
> >     <     >=    <=    ==【恒等号】    != 【不等于】 
>
> ```
>
> 使用场景：if语句，循环
>
> 代码演示：
>
> ```
> x = 3
> y = 5
> print(x > y)    #False
> print(x < y)
>
> print(x == y)
> print(x != y)
>
> print(x >= y)  #False
> print(x <= y)  #True
>
> ```

##### 2.4. 逻辑运算符

> and : 与
>
> or： 或
>
> not：非

##### 2.5. 成员运算符和身份运算符

> 成员运算符：
>
>  in, not in
>
> 身份运算符：
>
>  is, is not

##### 2.6. 位运算符【扩展】

> 前提：将数字转换为二进制使用
>
> &【按位与】 |【按位或】 ^【按位异或】 ~【按位取反】 << 【左移】 >>【右移】
>
> 代码演示：
>
> ```python
> print(6 & 3)
> print(6 | 3)
> print(6 ^ 3)
> print(~6)
> print(6 << 2)
> print(6 >> 2)
> ```

### 三、循环控制语句 （if for while）

#### 1. if语句

##### 1.1简单if语句【单分支】

语法：

if 表达式：

 执行语句



##### 1.2if-else语句【双分支】

> 语法：
>
> if 表达式：
>
>  执行语句1
>
> else:
>
>  执行语句2



##### 1.3if-elif-else语句【多分支】

> 语法：
>
> if 表达式1：
>
>  执行语句1
>
> elif 表达式2：
>
>  执行语句2
>
> elif 表达式3：
>
>  执行语句3
>
> 。。。。。
>
> else:
>
>  执行语句n

##### 1.4 嵌套if语句

> 语法：
>
> if 表达式1：
>
>    执行语句1
>
>    if 表达式2：
>
> ​      执行语句2

#### 2. for循环语句

> 语法：
>
> for 变量名 in 可迭代对象：
>
>  循环体

#### 3. while循环语句



> 语法：
>
> 初始化表达式
>
> while 条件表达式：
>
> ​    循环体
>
> ​    循环之后操作表达式

#### 4. break、continue和pass语句的使用



### 四、函数

#### 1.函数概述

##### 1.1认识函数

> 需求:求圆的面积
>
> s = π * r ** 2
>
> ```
> c = math.sqrt(a**2 + b**2)
>
> ```
>
> 代码演示：
>
> ```
> r1 = 6.8
> s1 = 3.14 * r1 ** 2
>
> r2 = 10
> s1 = 3.14 * r2 ** 2
>
> r3 = 2
> s1 = 3.14 * r3 ** 2
>
> r4 = 30
> s1 = 3.14 * r4 ** 2
>
> #define
> def test(r):
>   s = 3.14 * r * 2
>     
> test(6.8)
> test(10)
> test(30)
>
> ```
>
> 问题:代码重复
>
>  后期维护成本太高
>
>  代码可读性不高
>
> 解决问题：函数
>
> 在一个完整的项目中，某些功能会被反复使用，那么将这部分功能对应的代码提取出来，当需要使用功能的时候直接使用
>
> 本质：对一些特殊功能的封装
>
> 优点：
>
>  a.简化代码结构，提高应用的效率
>
>  b.提高代码复用性
>
>  c.提高代码的可读性和可维护性
>
> 建议：但凡涉及到功能，都尽量使用函数实现

##### 1.2定义函数

> 语法：
>
> def 函数名(参数1，参数2，参数3....):
>
>  函数体
>
>  返回值
>
> 说明：
>
> a.函数由两部分组成：声明部分和实现部分
>
> b.def,关键字，是define的缩写，表示定义的意思
>
> c.函数名：类似于变量名，遵循标识符的命名规则，尽量做到顾名思义
>
> d.（）：表示的参数列表的开始和结束
>
> e.参数1，参数2，参数3.... ：参数列表【形式参数，简称为形参】，其实本质上就是一个变量名，参数列表可以为空
>
> f.函数体：封装的功能的代码
>
> g.返回值：一般用于结束函数，可有可无，如果有返回值，则表示将相关的信息携带出去，携带给调用者，如果没有返回值，则相当于返回None
>
> 

#### 2.使用函数

##### 2.1简单函数

> 无参无返回值的函数
>
> 代码演示：
>
> ```
> #1.无参无返回值的函数
> #函数的声明部分
> def test():
>     #函数的实现部分
>     #函数体
>     print("hello")
>
> ```

##### 2.2函数的调用

> 定义好函数之后，让函数执行
>
> 格式：函数名(参数列表)
>
> 代码演示：
>
> ```
> #print(num)
> #test()
>
> #1.无参无返回值的函数
> #函数的声明部分
> def test():
>     #函数的实现部分
>     #函数体
>     #print("hello")
>     for i in range(10):
>         print(i)
>
> def test():
>     print("~~~~~~")
>
> #注意1：当定义好一个函数之后，这个函数不会自动执行函数体
>
> #2.函数的调用
> #格式：函数名(参数列表)
> #注意2：当调用函数的时候，参数列表需要和定义函数时候的参数列表保持一致
> #注意3：一个函数可以被多次调用
> test()
> test()
> test()
> test()
>
> #3.注意4：当在同一个py文件中定义多个同名的函数，最终调用函数，调用的最后出现的函数【覆盖：函数名类似于变量名，相当于变量的重新赋值】
> #4.注意5：自定义函数必须先定义，然后才调用，否则报NameError
>
> ```

> 函数的调用顺序：
>
> ```
> #函数调用
> #1.在一个自定义的函数内部也可以调用函数
> #2.函数调用的顺序
> def test1():
>     print("aaaa")
>     test2()
>     print("over")
>
> def test2():
>     print("bbbb")
>     test3()
>     test4()
>
> def test3():
>     print("cccc")
>
> def test4():
>     print("dddd")
>
> test1()
>
> #注意：函数在调用的过程中，相互之间的关系，以及代码执行的先后顺序
>
> ```

##### 2.3函数中的参数

> 参数列表：如果函数所实现的功能涉及到未知项参与运算，此时就可以将未知项设置为参数
>
> 格式：参数1,参数2.....
>
> 分类：
>
>  形式参数：在函数的声明部分，本质就是一个变量，用于接收实际参数的值 【形参】
>
>  实际参数：在函数调用部分，实际参与运算的值，用于给形式参数赋值 【实参】
>
>  传参：实际参数给形式参数赋值的过程，形式参数 = 实际参数
>
> 代码演示：
>
> ```
> #传参：实际参数给形式参数赋值的过程，形式参数 = 实际参数
>
> #需求：给函数一个姓名和一个年龄，在函数内部将内容打印出来
> def myPrint(name,age):
>     print("姓名：%s,年龄：%d"%(name,age))
>
> #调用函数
> str = "zhangsan"
> num = 19
> myPrint(str,num)
>
> """
> 传参：
> 实参给形参赋值
> name = "zhangsan"
> age = 19
> """
>
> #需求：求两个数的和
> def add(num1,num2):
>     sum = num1 + num2
>     print(sum)
>
> add(10,20)
> add(33,2)
>
> #TypeError: add() missing 2 required positional arguments: 'num1' and 'num2'   实参和形参不匹配
>
> ```
>
> 形参和实参之间的关系：
>
> ```
> #需求：交换两个变量的值
> def exchange(num1,num2):
>     temp = num1
>     num1 = num2
>     num2 = temp
>     print("exchange函数内部：num1=%d num2=%d"%(num1,num2))
>
> num1 = 11
> num2 = 22
> exchange(num1,num2)
> print("外面：num1=%d num2=%d" % (num1, num2))
>
> #1.实参和形参重名对函数实现没有影响
> #2.进行传参之后，实际参与运算的是形参，对实参没有影响【将形参可以理解为实参的替代品】
> #3.本质原因：形参和实参在内存中开辟的空间不同
>
> ```

##### 2.4值传递和引用传递【面试题】

> 值传递：传参的过程中传递的是值，一般指的是不可变的数据类型，number,tuple,string
>
> 引用传递：传参的过程中传递的是引用，一般指的是可变的数据类型，list，dict,set
>
> 代码演示：
>
> ```
> #值传递
> def func1(a):
>     a = 10
>
> temp = 20
> #传参：temp,但实际上传的是20
> func1(temp)
> print(temp)   #20
>
>
> #引用传递
> def func2(list1):
>     list1[0] = 100
>
> l = [10,20,30,40]
> func2(l)    #list1 = l
> print(l[0])
>
>
> """
> l = [10,20,30,40]
> list1 = l
> list1[0] = 100
>
> """
>
> ```
>
> 总结：
>
> 引用传递本质上传递的是内存地址

##### 2.5参数的类型【掌握】

> a.必需参数
>
>  调用函数的时候必须以正确的顺序传参，传参的时候参数的数量和形参必须保持一致
>
> 代码演示：
>
> ```
> #1.必需参数
> def show1(str1,num1):
>     print(str)
>
> show1("hello",10)
> #show1()
> #如果形参没有任何限制，则默认为必需参数，调用函数的时候则必需传参，顺序一致，数量一致
>
> ```
>
> b.关键字参数
>
>  使用关键字参数允许函数调用的时候实参的顺序和形参的顺序可以不一致，可以使用关键字进行自动的匹配
>
> 代码演示：
>
> ```
> #2.关键字参数
> def show2(name,age):
>     age += 1
>     print(name,age)
>
> #正常调用
> show2("abc",10)
> #show2(10,"abc")
>
> #关键字参数调用函数
> #注意1：关键字参数中的关键字其实就是形参的变量名，通过变量名进行传参
> show2(age = 20,name = "lisi")
> show2(name = "lisi",age = 20)
>
> #注意2：关键字参数只有一个的情况下，只能出现在参数列表的最后
> show2("lisi",age = 30)
>
> #错误演示
> #show2(40,name = "lisi")   TypeError: show2() got multiple values for argument 'name'
> #show2(name = "lisi",40)
>
> #系统的关键字参数
> print("",end=" ")
>
> ```
>
> c.默认参数
>
>  调用函数的时候，如果没有传递参数，则会使用默认参数
>
> 代码演示：
>
> ```
> #3.默认参数
> #注意1：在形参设置默认参数，如果传参，则使用传进来的数据，如果不传参，则使用默认数据
> def fun1(name,age=18):
>     print(name,age)
>
> fun1("zhangsan",20)
> fun1("lisi")
> fun1(name = "abc",age = 33)
> fun1(name = "hello")
>
> #注意2：在参数列表中，如果所有的形参都是默认参数，正常使用；但是，如果默认参数值只有一个，则只能出现在参数列表的最后面
> def fun2(num1 = 10,num2 = 20):
>     print(num1.num2)
>
> ```
>
> d.不定长参数
>
>  可以处理比当初声明时候更多的参数 * **
>
> 代码演示：
>
> ```
> #4.不定长参数【可变参数】
> #4.1   *   ：被当做tuple处理，变量名其实就是一个元组名
> #注意1：传参的时候，实参可以根据需求任意传参,数量不确定
> #注意2:定义不定长参数时，最好将不定长参数放到参数列表的最后面【如果不定长参数出现在参数列表的前面，则在实参列表中使用关键字参数】
> def func1(name,*hobby):
>     print(name)
>     print(hobby)
>     print(type(hobby))   #<class 'tuple'>
>
>     #遍历
>     for element in hobby:
>         print(element)
>
> func1("aaa","anc","aaa","5435","tesrg","gtsrhesh",10,True)
>
> # 4.2  **   :被当做字典处理，变量名就相当于字典名
> def func2(**args):
>     print(args)
>     print(type(args))   #<class 'dict'>
>
>     for k,v in args.items():
>         print(k,v)
>
> #注意1：使用**的时候，实参就必须按照key=value的方式进行传参
> func2(x = 10,y = 20)
>
> ```

##### 2.6函数的返回值

> 作用：表示一个函数执行完毕之后得到的结果
>
> 使用:return,表示结束函数，将函数得到的结果返回给调用者
>
> 代码演示：
>
> ```
> #1.结束函数，返回数据
> #需求：求两个整数的和，并返回
> def add(num1,num2):
>     sum1 = num1 + num2
>     #print(sum1)
>
>     #将结果返回给调用者
>     return sum1
>
>     #注意：在同一个代码块中，如果在return后面出现语句，则永远不会被执行
>     #print("hello")
>
>
> #注意：如果一个函数由返回值，要么采用变量将返回值接出来，要么将整个函数的调用直接参与运算
> r = add(10,20)
> print(r)
> print(add(10,20))   #30
> #print("~~~~",sum1)
>
> total = add(1,2) + 5
> print(total)    #8
>
>
> def func(num1,num2):
>     sum2 = num1 + num2
>
>
> #注意：如果一个函数没有返回值，则整体计算的结果为None
> #print(func(10,20))
>
> #如果一个函数没有返回值，则这个函数的调用不能直接参与运算
> total1 = func(1,2) + 5  #TypeError: unsupported operand type(s) for +: 'NoneType' and 'int'
> print(total1)
>
> ```
>
> 在分支语句中使用return
>
> ```
> #2.如果一个函数体中有分支，设置了返回值，最好每一个分支都有一个返回值
> #需求：输入两个数，比较两个数的大小，返回较大的一个
> def compare(num1,num2):
>     if num1 > num2:
>         return num1
>     elif num1 < num2:
>         return num2
>     else:
>         return True,num1
>
> result = compare(12,12)
> print(result)
>
> #注意1：在Python中，不同分支返回的数据类型可以是不相同的
> #注意2;在Python中，一个return可以同时返回多个数据，被当做元组处理
>
> ```

> 总结：
>
> 自定义一个函数
> 是否需要设置参数：是否有未知项参与运算
>
> 是否需要设置返回值：是否需要在函数外面使用函数运算之后的结果

> 函数使用练习：
>
> ```
> #需求1：封装函数功能，统计1~某个数范围内能被3整除的数的个数
> """
> 参数：某个数
> 返回值：可设置可不设置
> """
> def getCount(num):
>     count = 0
>     for i in range(num + 1):
>         if i % 3 == 0:
>             count += 1
>
>     #print(count)
>     return count
>
> r1 = getCount(1000)
> print(r1)
> r2 = getCount(100)
> print(r2)
>
>
> #需求2：封装函数功能，判断某年是否是闰年
> """
> 参数：某年
> 返回值：可设置可不设置
> """
> def isLeapYear(year):
>     if (year % 4 == 0 and year % 100 != 0) or year % 400 == 0:
>         #print("闰年")
>         #return "闰年"
>         return  True
>     else:
>         #print("平年")
>         #return "平年"
>         return False
>
> result = isLeapYear(2020)
> print(result)
>
> ```

#### 3.匿名函数【掌握】

> 不再使用def这种的形式定义函数，使用lambda来创建匿名函数
>
> 特点：
>
>  a.lambda只是一个表达式，比普通函数简单
>
>  b.lambda一般情况下只会书写一行，包含参数，实现体，返回值
>
> 语法:lambda 参数列表 ： 实现部分
>
> 代码演示：
>
> ```
> #语法:lambda 参数列表 ： 实现部分
>
> #1.
> #需求：求两个数的和
> #普通函数
> def add(num1,num2):
>     sum = num1 + num2
>
> add(num1 = 10,num2 = 20)
>
> #匿名函数本身是没有函数名，将整个lambda表达式赋值给一个变量，然后将这个变量当做函数使用
> sum1 = lambda n1,n2:n1 + n2
> print(sum1(10,20))
>
> #2.在匿名函数中也可以使用关键字参数
> g = lambda  x,y:x ** 2 + y ** 2
> print(g(3,4))
> print(g(x = 3,y = 4))
>
> #3.在匿名函数中也可以使用默认参数
> h = lambda  x=0,y=0 : x ** 2 + y ** 2
> print(h())
> print(h(10))
> print(h(10,20))
> ```