


class machine8:

    @staticmethod
    def repeat_lo(base):
        def decorated(self, lo):
            if lo == 0:
                lo = self.func[self.fptr]
                self.fptr += 1
            base(self, lo)
        return decorated

    @staticmethod
    def get_literals(base):
        def decorated(self, lo):
            literals = self.func[self.fptr:self.fptr + lo]
            self.fptr += lo
            base(self, literals)
        return decorated

    def __init__(self, main):
        self.func = main;
        self.fptr = 0;
        self.stack = [];
        self.call_stack = [];
        self.reg = [];

    def get(self, lo):
        return self.stack[len(self.stack) - lo]

    def pop(self, lo):
        return self.stack.pop(len(self.stack) - lo)

    def jump(self, lo):
        byte = self.stack[-1]
        if lo & 8:
            self.stack.pop()
        if lo & 7 == 7:
            jump = True
        elif byte == 0:
            jump = lo & 1
        elif byte  > 0:
            jump = lo & 2
        elif byte <  0:
            jump = lo & 4
        if jump:
            self.fptr += self.stack[self.fptr]

    @repeat_lo
    @get_literals
    def cpush(self, literals):
        for byte in literals:
            self.stack.append(byte)

    def push(self, lo):
        self.stack.append(self.get(lo))

    def pull(self, lo):
        if lo:
            self.stack.append(self.pop(lo))
        else:
            lo = self.func[self.fptr]
            self.func += 1
            self.push(lo)  # special case to turn a no-op into lpush

    def bury(self, lo):
        lo = lo or 16  # turn no-op into useful special tool for accessing 16th element
        el = self.stack.pop()
        self.stack.insert(len(self.stack) - lo, el)

    def math(self, lo):
        if lo < 9:
            a, b = self.stack.pop(), self.stack.pop()
            if lo == 0:
                self.stack.append(a + b)
            elif lo == 1:
                self.stack.append(a - b)
            elif lo == 2:
                self.stack.append(a * b)
            elif lo == 3:
                self.stack.append(a // b)
            elif lo == 4:
                self.stack.append(a % b)
            elif lo == 5:
                self.stack.append(a // b)
                self.stack.append(a % b)
            elif lo == 6:
                self.stack.append(a | b)
            elif lo == 7:
                self.stack.append(a & b)
            elif lo == 8:
                self.stack.append(a ^ b)
            elif lo == 9:
                self.stack.append(a >> b)
            elif lo == 10:
                self.stack.append(a << b)
        else:
            a = self.stack.pop()
            if lo == 11:
                self.stack.append(a + 1)
            elif lo == 12:
                self.stack.append(a - 1)
            elif lo == 13:
                self.stack.append(~a)
            elif lo == 14:
                self.stack.append(-a)
            elif lo == 15:
                self.stack.append(1 if a else 0)

    @staticmethod
    def call_result(func):
        def decorated(self, *args, **kwargs):
            self.call_stack.append((self.func, self.fptr))
            self.func = func(self, *args, **kwargs)
            self.fptr = 0
        return decorated

    @call_result
    def call(self, lo):
        return self.get(lo)
        
    def code(self, options):
        def do_code(byte):
            self.code.extend(self.rcode[::-1])
            self.code.append(byte)
            self.rcode = []
        def do_rcode(byte):
            self.rcode.append(byte)
        code_adder = do_rcode if 'r' in options else do_code
        def do_ccode(lo):
            if lo == 0:
                lo = self.func[self.fptr]
                self.fptr += 1
            for i in lo:
                code_adder(self.func[self.fptr])
                self.fptr += 1
        def do_pcode(lo):
            code_adder(self.get(lo))
        return do_ccode if 'c' in options else do_pcode

    @call_result
    def pcall(self):
        return self.stack.pop()
    
    @call_result
    def ccall(self):
        ret = self.func[self.fptr]
        self.fptr += 1
        return ret
    
    
    def ret(self):
        self.func, self.fptr = self.call_stack.pop()
    
    def flush(self):
        self.code.extend(self.rcode[::-1])
        self.stack.append(self.code)
        self.code = []
        self.rcode = []
    
    def push_this(self):
        self.stack.append(self.func)
    
    def lo_op(self):
        lo_ops = [
            self.ret,       # 0
            
            self.pcall,     # 1
            self.ccall,     # 2
            
            self.flush,     # 3
            self.push_this, # 4
        ]


    def __iter__(self):
        hi_ops = [
            self.jump,      # 0 change fptr

            self.cpush,     # 1 add constants to the stack (note LIFO)
            self.push,      # 2 copy an element to the top of the stack
            self.pop,       # 3 delete an element from the stack
            self.pull,      # 4 move an element to the top of the stack and push the rest back
            self.bury,      # 5 push the top element down the stack, pulling the rest back

            self.math,      # 6 arithmetic

            self.call,      # 7 call a function, after which resume execution
            self.code('c'), # A add bytes to the code register
            self.code('rc'),# B insert bytes after the last normal code or ccode execution
            self.code(''),  # 8 add a byte from the stack to the code register
            self.code('r'), # 9 insert a byte from the stack after the last normal code or ccode execution
            self.lo_op(),   # C

            self.input,     # D
            self.output,    # E
        ]
        while self.call_stack or self.fptr < len(self.func):
            while self.fptr < len(self.func):
                byte = self.func[self.fptr]
                hi = byte >> 4
                lo = byte & 0x0F
                self.fptr += 1
                hi_ops[hi](lo)


            self.ret()



