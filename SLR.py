class Id:
    """A terminal or nonterminal."""
    alphabet = set()
    is_empty_calculated = False
    is_first_calculated = False
    is_follow_calculated = False
    def __init__(self, name):
        self.name = name
        self.prods = []     #list<Prod>
        #self.get_follow()  #self.follow : set<terminal>
        Id.alphabet.add(self)
        #self.source = [] #list<tuple<id_idx:int, prod_idx:int, places:tuple<int>>>
        self.empty = None
        self.first = None
        self.follow = None

    def __str__(self):
        return self.name

    def __repr__(self):
        return str(self)

    def __eq__(self, other):
        return self.name == other.name

    def __hash__(self):
        return hash(self.name)

    def add_prod(self, *new_prods):
        self.prods.extend(new_prods)

    def has_prod(self,prod):
        return prod in self.prods

    def get_prods(self):
        return self.prods

    def isterminal(self):
        return len(self.prods) == 0

    def isdollar(self):
        return str(self) == '$'
    
    def isepsilon(self):
        return str(self) == 'ε'

    @classmethod
    def calc_empty(cls):
        """terminal_a.empty = false; ε.empty = true"""
        for id in Id.alphabet:
            if id.isepsilon():
                id.empty = True
            elif id.isterminal():
                id.empty = False
            else:
                id.empty = False     #set to False temporarily
        while(True):
            change = False
            for id in Id.alphabet:
                if id.isterminal() or id.empty:
                    continue
                for p in id.prods:
                    empty_p = True
                    for i in p.ids:
                        if i.empty == False:
                            empty_p = False
                            break
                    if empty_p == True:
                        id.empty = True
                        break
                if id.empty == True:
                    change = True
            if change == False:
                break
        cls.is_empty_calculated = True

    @classmethod
    def calc_first(cls):
        """PS: FIRST{ε} = ∅, FIRST(terminal_a) = {terminal_a}"""
        if not cls.is_empty_calculated:
            cls.calc_empty()
        for id in cls.alphabet:
            if id.isepsilon():
                id.first = set()
            elif id.isterminal():
                id.first = set([id])
            else:
                id.first = set() # just initialization
        while True:
            change = False
            for id in cls.alphabet:
                if id.isterminal():
                    continue
                for p in id.prods:
                    id_first_size_before = len(id.first)
                    id.first |= p.get_first() #整个产生式右部的FIRST
                    if id_first_size_before != len(id.first):
                        change = True
            if change == False:
                break
        cls.is_first_calculated = True  #标记已经计算完成，之后不用重新计算

    @classmethod
    def calc_follow(cls):
        """FOLLOW(terminal) = None, FOLLOW(nonterminal) = set<terminal>."""
        if not cls.is_first_calculated: 
            cls.calc_first()        #如果还没有计算empty的话，也会被calc_first一并计算
        for id in cls.alphabet:
            if id.isterminal():
                id.follow = None
            else:
                id.follow = set() # just initialization
        while True:
            change = False
            for id in cls.alphabet:
                for p in id.prods:
                    for idx,i in enumerate(p.get_ids()):
                        if not i.isterminal():
                            i_follow_size_before = len(i.follow)
                            if p.isempty(start = idx+1):    #如果后面的部分可能推导为空
                                i.follow |= id.follow       #加入产生式左部的FOLLOW
                            i.follow |= p.get_first(start = idx+1) #加入后面的部分的FIRST
                            if i_follow_size_before != len(i.follow):
                                change = True
            if change == False:
                break
        Id.is_follow_calculated = True

    def get_first(self):
        return self.first

    def get_follow(self):
        return self.follow

class Prod:
    """ The right side of the production. list<Id>. Immutable."""
    def __init__(self, *ids):
        assert isinstance(ids[0],Id)
        self.ids = list(ids)
    
    def __str__(self):
        return ' '.join([str(id) for id in self.ids])

    def __eq__(self, other):
        for a,b in zip(self.ids, other.ids):
            if a != b:
                return False
        return True
    def __len__(self):
        return len(self.ids)

    def __hash__(self):
        return hash(str(self))

    def get_ids(self):
        return self.ids

    def get_first(self,start=0):
        """Get the FIRST set of a subsequence of prod. [start, length)"""
        assert start>=0 and start <= len(self)
        if not Id.is_empty_calculated:      #请不要在Id.calc_empty中调用
            Id.calc_empty()
        # Maybe Id.is_first_calculated should be checked too
        ans = set()
        for id in self.ids[start:]:
            ans |= id.get_first()
            if not id.empty:
                break
        return ans
    
    def isempty(self, start = None, end = None):
        """[start,end)"""
        if not Id.is_empty_calculated:  #只使用计算好的empty，所以请不要在Id.calc_empty中调用这个函数。
            Id.calc_empty()
        if start is None:
            start = 0
        if end is None:
            end = len(self)
        ans = True
        for id in self.ids[start:end]:
            if not id.empty:
                ans = False
                break
        return ans

class Item:
    """ A production with a dot."""
    def __init__(self, left, prod, dot:int):
        assert isinstance(left, Id) and not left.isterminal()
        assert isinstance(prod,Prod)
        assert dot >= 0 and dot <= len(prod)
        assert left.has_prod(prod)
        
        self.left = left
        self.prod = prod
        self.dot = dot

    def feed(self,id):
        if self.dot >= len(self.prod):
            return None,1                     # 归约
        if self.prod.ids[self.dot] != id:
            return None,-1                     # 匹配失败
        return Item(self.left, self.prod, self.dot + 1),0   #移进
    
    def __str__(self):
        return str(self.left) + ' → ' + ' '.join([str(id) for id in self.prod.ids[:self.dot]]) + ' · ' + ' '.join([str(id) for id in self.prod.ids[self.dot:]])
    
    def __eq__(self, other):
        return self.left == other.left and self.prod == other.prod

    def __hash__(self):
        return hash(str(self))

    def closure_1step(self):
        """return set<Item>"""
        if self.dot >= len(self.prod) or self.prod.ids[self.dot].isterminal():
            return set()
        target = self.prod.ids[self.dot]
        return set([Item(target, prod,0) for prod in target.get_prods()])
    
class Node:
    """ A list of items."""
    nodes = []
    def __init__(self, items):
        self.items = set(items)
        self.make_closure()
        isvisited = self.register()     #self.uid
        if not isvisited:
            self.get_neighbors()    #self.neighbors

    def __str__(self):
        return ''.join([str(item)+'\n' for item in self.items])
    
    def __eq__(self, other):
        return self.items == other.items    #集合之间根据元素的__eq__来判等

    def make_closure(self):
        """make the self.items a closure."""
        while(True):
            length_before = len(self.items)
            off_springs = set()
            for item in self.items:
                off_springs |= item.closure_1step()  #这里可以再优化效率
            self.items |= off_springs
            length_after = len(self.items)
            if length_before==length_after:
                break
            
    def register(self):
        if len(self.items) == 0:
            self.uid = -1
            return True
        if self in Node.nodes:
            self.uid = Node.nodes.index(self)
            return True 
        else:
            self.uid = len(Node.nodes)
            Node.nodes.append(self)
            return False

    def feed(self,id):
        new_items = []
        st_code_set = set()
        for item in self.items:
            fed_item, st_code = item.feed(id)
            if fed_item is not None:
                new_items.append(fed_item)
            st_code_set.add(st_code)                # To be continue...
        return Node(new_items)

    def get_neighbors(self):
        self.neighbors = dict()
        for id in Id.alphabet:
            neighbor = self.feed(id)
            self.neighbors[id] = neighbor.uid

class SLR:
    pass

if __name__ == "__main__":
    a = [Id("E'"),Id("E"),Id("T"),Id("F"),Id("+"),Id("*"),Id("a"),Id("b"),Id("ε"),Id("$")]  #alphabet, the last two must be "ε" and "$"
    def add_prod(idx, *idxes):
        ids = [a[i] for i in idxes]
        return a[idx].add_prod(Prod(*ids))
    add_prod(0,1,-1)
    add_prod(1,1,4,2)
    add_prod(1,2)
    add_prod(2,2,3)
    add_prod(2,3)
    add_prod(3,3,5)
    add_prod(3,6)
    add_prod(3,7)

    Id.calc_follow()    #ugly!!!

    start_node = Node([Item(a[0],a[0].get_prods()[0],0)])

    for id in Id.alphabet:
        print(id.name)
        print(id.empty)
        print(id.first)
        print(id.follow)
        print("-"*36)

    for node in Node.nodes:
        print("[%d]"%node.uid)
        print(node)
        print(node.neighbors)
        print('='*36)
    
