class Id:
    """A terminal or nonterminal."""
    def __init__(self, name, parser):
        self.name = name
        self.prods = set() # usage: iterate, add, in.
        self.parser = parser
        self.register(parser)
        self.empty = None
        self.first = None
        self.follow = None
    
    def register(self,parser):
        """register itself in parser.alphabet and parser.uid_dict; also, set self.uid"""
        if self.name not in parser.uid_dict:
            self.uid = len(parser.alphabet)
            parser.alphabet.append(self)
            parser.uid_dict[self.name] = self.uid

    def __str__(self):
        return self.name

    def __repr__(self):
        return str(self)

    def __eq__(self, other):
        return self.name == other.name

    def __hash__(self):
        return hash(self.name)

    def add_prod(self, new_prod):
        self.prods.add(new_prod)

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

    def get_first(self):
        return self.first

    def get_follow(self):
        return self.follow

class Prod:
    """ The right side of the production. list<Id>. Immutable."""
    def __init__(self, ids):
        assert isinstance(ids,list)
        self.ids = ids
    
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
        ans = set()
        for id in self.ids[start:]:
            ans |= id.get_first()
            if not id.empty:
                break
        return ans
    
    def isempty(self, start = None, end = None):
        """[start,end)"""
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
    def __init__(self, items, parser):
        self.items = set(items)
        self.make_closure()
        self.parser = parser
        isvisited = self.register(parser)     #self.uid
        self.neighbors = None
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
            
    def register(self,parser):
        if len(self.items) == 0:
            self.uid = -1
            return True
        if self in parser.nodes: #是否有效排重了???
            self.uid = parser.nodes.index(self)
            return True 
        else:
            self.uid = len(parser.nodes)
            parser.nodes.append(self)
            return False

    def feed(self,id):
        new_items = []
        st_code_set = set()
        for item in self.items:
            fed_item, st_code = item.feed(id)
            if fed_item is not None:
                new_items.append(fed_item)
            st_code_set.add(st_code)                # To be continue...
        return Node(new_items,self.parser)

    def get_neighbors(self):
        self.neighbors = dict()
        for id in self.parser.alphabet:
            neighbor = self.feed(id)
            self.neighbors[id] = neighbor.uid

class Parser:
    pass

class SLR(Parser):
    def __init__(self, bnf:str):
        self.is_empty_calculated = False
        self.is_first_calculated = False
        self.is_follow_calculated = False
        self.alphabet = [] # list<Id>
        self.uid_dict = {} # dict<str, int>
        self.start_id = None
        self.analyze(bnf)

        self.nodes = []
        self.generate_nodes()

    def generate_nodes(self):
        Node(
            [Item(
                self.start_id,
                list(self.start_id.get_prods())[0],
                0
            )],
            self
        )

    def analyze(self,bnf):
        # 对于每个标识符，应只生成一个Id实例（尽量使用get_id_by_name接口构造）。
        # 在读取文法并构建数据结构时，应该只从alphabet中取需要的Id对象。
        # 注册新Id对象到alphabet和uid_dict的工作已在Id的构造函数中完成。
        # 文法允许有重复的产生式。
        # 文法允许使用‘|’
        # 读完之后alphabet、uid_dict都应构造完成，Id及其prods也构造完成。
        lines = bnf.split('\n')
        for line in lines:
            sp_line = self.sp(line)
            if len(sp_line) >= 3:
                name = sp_line[0]
                if name not in self.uid_dict:
                    id = Id(name,self)
                else:
                    id = self.get_id_by_name(name)
                prod_strs = ' '.join(sp_line[2:]).split('|')
                for prod_str in prod_strs:
                    names = self.sp(prod_str)
                    print(names)
                    if '$' in names:
                        self.start_id = id
                    prod = self.generate_prod_with_names(names)
                    id.add_prod(prod)
    
    def generate_prod_with_names(self,names):
        ans = []
        for name in names:
            ans.append(self.get_id_by_name(name))
        return Prod(ans)

    def get_id_by_name(self,name):
        # 需要Id对象时应尽量从该接口获取
        # 如果已经构建过了就直接从alphabet中取
        # 如果没有，则新构建一个
        if name in self.uid_dict:
            return self.alphabet[self.uid_dict[name]]
        else:
            return Id(name,self)
        
    def sp(self, s, separator = ['\t',' ','\n']):
        """Split a string with multiple characters"""
        ans=[]
        i=j=0
        while j<len(s) and s[j] in separator:
            j+=1
        i=j
        while i<len(s):
            while j<len(s) and s[j] not in separator:
                j+=1
            ans.append(s[i:j])
            while j<len(s) and s[j] in separator:
                j+=1
            i=j
        return ans
    
    def calc_empty(self):
        """terminal_a.empty = false; ε.empty = true"""
        for id in self.alphabet:
            if id.isepsilon():
                id.empty = True
            elif id.isterminal():
                id.empty = False
            else:
                id.empty = False     #set to False temporarily
        while(True):
            change = False
            for id in self.alphabet:
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
        self.is_empty_calculated = True

    def calc_first(self):
        """PS: FIRST{ε} = ∅, FIRST(terminal_a) = {terminal_a}"""
        if not self.is_empty_calculated:
            self.calc_empty()
        for id in self.alphabet:
            if id.isepsilon():
                id.first = set()
            elif id.isterminal():
                id.first = set([id])
            else:
                id.first = set() # just initialization
        while True:
            change = False
            for id in self.alphabet:
                if id.isterminal():
                    continue
                for p in id.prods:
                    id_first_size_before = len(id.first)
                    id.first |= p.get_first() #整个产生式右部的FIRST
                    if id_first_size_before != len(id.first):
                        change = True
            if change == False:
                break
        self.is_first_calculated = True  #标记已经计算完成，之后不用重新计算

    def calc_follow(self):
        """FOLLOW(terminal) = None, FOLLOW(nonterminal) = set<terminal>."""
        if not self.is_first_calculated: 
            self.calc_first()        #如果还没有计算empty的话，也会被calc_first一并计算
        for id in self.alphabet:
            if id.isterminal():
                id.follow = None
            else:
                id.follow = set() # just initialization
        while True:
            change = False
            for id in self.alphabet:
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
        self.is_follow_calculated = True

class LR(Parser):
    pass

class LALR(Parser):
    pass

if __name__ == '__main__':
    with open('test.bnf', 'r') as f:
        lines = f.readlines()
        bnf = '\n'.join(lines)
        print(bnf,'\n'+'%'*36)

        slr = SLR(bnf)
        print(slr.alphabet)
        print(slr.uid_dict)
        for node in slr.nodes:
            print(node)
            print(node.neighbors)
            print("="*36)