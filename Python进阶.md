#### 迭代器

```python
class Range:
    def __init__(self, start, end=None, step=1):
        if end is None:
            self.end = start
            self.start = 0
        else:
            self.start = start
            self.end = end
        self.step = step

    def __iter__(self):
        return self

    def __next__(self):
        if self.start < self.end:
            current = self.start
            self.start += self.step
            return current
        else:
            raise StopIteration()
```

- iterator: 任何实现了 `__iter__` 和 `__next__` 方法的对象都是迭代器.
    * `__iter__` 得到一个迭代器。迭代器的`__iter__()`返回自身
    * `__next__` 返回迭代器下一个值
    * 如果容器中没有更多元素, 则抛出 StopIteration 异常
    * Python2中没有 `__next__()`, 而是 `next()`

- `str / bytes / list / tuple / dict / set` 自身不是迭代器，他们自身不具备 `__next__()`, 但是具有 `__iter__()`, `__iter__()` 方法用来把自身转换成一个迭代器

- 练习1: 定义一个随机数迭代器, 随机范围为 [1, 50], 最大迭代次数 30

    ```python
    import random

    class RandomIter:
        def __init__(self, start, end, times):
            self.start = start
            self.end = end
            self.count = times

        def __iter__(self):
            return self

        def __next__(self):
            self.count -= 1
            if self.count >= 0:
                return random.randint(self.start, self.end)
            else:
                raise StopIteration()
    ```

#### 类方法和静态方法
- `method`

    - 通过实例调用
    - 可以引用类内部的**任何属性和方法**

- `classmethod`

    - 无需实例化
    - 可以调用类属性和类方法
    - 无法取到普通的成员属性和方法

- `staticmethod`

    - 无需实例化
    - **无法**取到类内部的任何属性和方法, 完全独立的一个方法

- 练习: 说出下面代码的运行结果

    ```python
    class Test(object):
        x = 123

        def __init__(self):
            self.y = 456

        def bar1(self):
            print('i am a method')

        @classmethod
        def bar2(cls):
            print('i am a classmethod')

        @staticmethod
        def bar3():
            print('i am a staticmethod')

        def foo1(self):
            print(self.x)
            print(self.y)
            self.bar1()
            self.bar2()
            self.bar3()

        @classmethod
        def foo2(cls):
            print(cls.x)
            print(cls.y) # 会报错
            cls.bar1() # 会报错,因为bar1是实例方法. 得通过self.bar1
            cls.bar2()
            cls.bar3()

        @staticmethod
        def foo3(obj):
            print(obj.x)
            print(obj.y)
            obj.bar1()
            obj.bar2()
            obj.bar3()

    t = Test()
    t.foo1()
    t.foo2()
    t.foo3()
    ```

#### 继承相关问题
- 什么是多态

    ```python
    class Animal:
        def run(self):
            print('animal running')

    class Lion(Animal):
        def run(self):
            print('lion running')

    class Tiger(Animal):
        def run(self):
            print('tiger running')

    class LionTiger(Lion, Tiger):
        pass

    cub = LionTiger()
    cub.run()
    isinstance(cub, Lion)
    isinstance(cub, Tiger)
    ```

- 多继承
    * 方法和属性的继承顺序: `Cls.mro()`
    * 菱形继承问题

        ```
        继承关系示意
        菱形继承
             A.foo()
           /   \
          B     C.foo()
           \   /
             D.mro()  # 方法的继承顺序，由 C3 算法得到
        ```

- super

    ```python
    class A:
        def __init__(self):
            print('enter A')
            self.x = 111
            print('exit A')

    class B(A):
        def __init__(self):
            print('enter B')
            self.y = 222
            A.__init__(self)
            # super().__init__()
            print('exit B')

    class C(A):
        def __init__(self):
            print('enter C')
            self.z = 333
            A.__init__(self)
            # super().__init__()
            print('exit C')

    class D(B, C):
        def __init__(self):
            print('enter D')
            B.__init__(self)
            C.__init__(self)
            # super().__init__()
            print('exit D')

    d = D()
    ```




#### 魔术方法
1. `__str__` 格式化输出对象
2. `__init__` 和 `__new__`

    * `__new__` 创建一个实例，并返回类的实例
    * `__init__` 初始化实例，无返回值
    * `__new__` 是一个特殊的类方法,不需要使用@classmethod来装饰.

        + 单例模式
            ```python
            class A(object):
                '''单例模式'''
                obj = None
                def __new__(cls, *args, **kwargs):
                    if cls.obj is None:
                        cls.obj = object.__new__(cls)
                    return cls.obj
            ```

3. 数学运算、比较运算
    * 运算符重载
        + `+`: `__add__(value)`
        + `-`: `__sub__(value)`   substract
        + `*`: `__mul__(value)`   mulply
        + `/`: `__truediv__(value)` (Python 3.x), `__div__(value)` (Python 2.x)  divide
        + `//`: `__floordiv__(value)`
        + `%`: `__mod__(value)`
        + `&`: `__and__(value)`
        + `|`: `__or__(value)`

    * 练习: 实现字典的 `__add__` 方法, 作用相当于 d.update(other)

        ```python
        class Dict(dict):
            def __add__(self, other):
                if isinstance(other, dict):
                    new_dict = {}
                    new_dict.update(self)
                    new_dict.update(other)
                    return new_dict
                else:
                    raise TypeError('not a dict')
        ```

    * 比较运算符的重载
        + `==`: `__eq__(value)` 
        + `!=`: `__ne__(value)`  
        + `>`: `__gt__(value)`
        + `>=`: `__ge__(value)`
        + `<`: `__lt__(value)`
        + `<=`: `__le__(value)`

    * 容器方法



    * `__len__` -> len

    * `__iter__` -> for

    * `__contains__` -> in

    * `__getitem__` 对 `string, bytes, list, tuple, dict` 有效

    * `__setitem__` 对 `list, dict` 有效

    * `__missing__` 对 dict 有效, 字典的预留接口, dict 本身并没有实现 

      ```python
      class Dict(dict):
          def __missing__(self, key):
              self[key] = None # 当检查到 Key 缺失时, 可以做任何默认行为
      ```

4. 可执行对象: `__call__`
5. 上下文管理 with:
    * `__enter__` 进入 `with` 代码块前的准备操作
    * `__exit__` 退出时的善后操作
    * 文件对象、线程锁、socket 对象 等 都可以使用 with 操作
    * 示例
      ```python
      class A:
          def __enter__(self):
              return self

          def __exit__(self, Error, error, traceback):
              print(Error, error, traceback)
      ```

6. `__setattr__, __getattribute__, __getattr__, __dict__`

    * 内建函数：`setattr(), getattr(), hasattr()`  python的内省.

    * 常用来做属性监听

        ```python
        class User:
            '''TestClass'''
            z = [7,8,9]
            def __init__(self):
                self.money = 10000
                self.y = 'abc'

            def __setattr__(self, name, value):
                if name == 'money' and value < 0:
                    raise ValueError('money < 0')
                print('set %s to %s' % (name, value))
                object.__setattr__(self, name, value)

            def __getattribute__(self, name):
                print('get %s' % name)
                return object.__getattribute__(self, name)

            def __getattr__(self, name):
                print('not has %s' % name)
                return -1

            def foo(self, x, y):
                return x ** y

        # 对比
        a = User()
        print(User.__dict__)
        print(a.__dict__)
        ```


