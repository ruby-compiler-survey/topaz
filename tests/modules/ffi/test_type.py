from tests.modules.ffi.base import BaseFFITest
from topaz.modules.ffi.type import type_names, W_TypeObject, VOID
from topaz.modules.ffi import type as ffitype

from rpython.rlib import clibffi
from rpython.rtyper.lltypesystem import rffi, lltype

# XXX maybe move to rlib/jit_libffi
from pypy.module._cffi_backend import misc

class TestType(BaseFFITest):
    def test_it_is_a_class(self, space):
        assert self.ask(space, "FFI::Type.is_a? Class")

    def test_builtin_is_a_type_subclass(self, space):
        w_res = space.execute("FFI::Type::Builtin.ancestors")
        w_type = space.execute("FFI::Type")
        assert w_type in self.unwrap(space, w_res)

    def test_it_has_these_attributes_on_the_low_level(self, space):
        w_type = W_TypeObject(space, 123)
        assert w_type.typeindex == 123

class TestFFI__TestType(BaseFFITest):
    def test_it_is_a_Module(self, space):
        assert self.ask(space, "FFI::NativeType.is_a? Module")

    def test_it_contains_some_type_constants(self, space):
        for typename in type_names:
            assert self.ask(space, "FFI::NativeType::%s.is_a? FFI::Type"
                            %typename)

    def test_it_has_these_instances_defined_as_constants(self, space):
        for typename in type_names:
            assert self.ask(space, "FFI::Type::%s.is_a? FFI::Type"
                            % typename)
            assert self.ask(space, "FFI::Type::%s.is_a? FFI::Type::Builtin"
                            % typename)

    def test_its_instances_can_be_accessed_in_different_ways(self, space):
        for typename in type_names:
            w_t1 = space.execute('FFI::TYPE_%s' % typename)
            w_t2 = space.execute('FFI::Type::%s' % typename)
            w_t3 = space.execute('FFI::NativeType::%s' % typename)
            assert w_t1 == w_t2
            assert w_t2 == w_t3

class TestFFI__Type_size(BaseFFITest):
    def test_it_returns_the_size_type(self, space):
        w_res = space.execute("FFI::Type::INT8.size")
        assert self.unwrap(space, w_res) == 1
        w_res = space.execute("FFI::Type::INT16.size")
        assert self.unwrap(space, w_res) == 2
        w_res = space.execute("FFI::Type::INT32.size")
        assert self.unwrap(space, w_res) == 4

class TestFFI__Type_eq(BaseFFITest):
    def test_it_compares_the_names(self, space):
        type1 = W_TypeObject(space, VOID)
        type2 = W_TypeObject(space, VOID)
        w_assertion = space.send(type1, '==', [type2])
        assert self.unwrap(space, w_assertion)

class Test_W_StringType(BaseFFITest):
    def test_it_reads_a_string_from_buffer(self, space):
        w_string_type = ffitype.W_StringType(space)
        charp_size = space.int_w(space.send(w_string_type, 'size'))
        data = lltype.malloc(rffi.CCHARP.TO, charp_size, flavor='raw')
        raw_str = rffi.str2charp("test")
        misc.write_raw_unsigned_data(data, raw_str, charp_size)
        w_res = w_string_type.read(space, data)
        assert space.is_kind_of(w_res, space.w_string)
        assert self.unwrap(space, w_res) == "test"
        lltype.free(data, flavor='raw')

    def test_it_writes_a_string_to_buffer(self, space):
        w_string_type = ffitype.W_StringType(space)
        charp_size = space.int_w(space.send(w_string_type, 'size'))
        data = lltype.malloc(rffi.CCHARP.TO, charp_size, flavor='raw')
        w_str = space.newstr_fromstr("test")
        w_string_type.write(space, data, w_str)
        raw_res = misc.read_raw_unsigned_data(data, charp_size)
        raw_res = rffi.cast(rffi.CCHARP, raw_res)
        assert rffi.charp2str(raw_res) == "test"
        lltype.free(data, flavor='raw')

class Test_W_PointerType(BaseFFITest):
    def test_it_reads_a_pointer_from_buffer(self, space):
        w_pointer_type = ffitype.W_PointerType(space)
        ptr_size = space.int_w(space.send(w_pointer_type, 'size'))
        data = lltype.malloc(rffi.CCHARP.TO, ptr_size, flavor='raw')
        raw_ptr = rffi.cast(lltype.Unsigned, 12)
        misc.write_raw_unsigned_data(data, raw_ptr, ptr_size)
        w_res = w_pointer_type.read(space, data)
        w_pointer_class = space.execute("FFI::Pointer")
        assert space.is_kind_of(w_res, w_pointer_class)
        assert self.unwrap(space, space.send(w_res, 'address')) == 12

    def test_it_writes_a_pointer_to_buffer(self, space):
        w_pointer_type = ffitype.W_PointerType(space)
        ptr_size = space.int_w(space.send(w_pointer_type, 'size'))
        data = lltype.malloc(rffi.CCHARP.TO, ptr_size, flavor='raw')
        w_ptr = space.execute("FFI::Pointer.new(15)")
        w_pointer_type.write(space, data, w_ptr)
        raw_res = misc.read_raw_unsigned_data(data, ptr_size)
        raw_res = rffi.cast(lltype.Unsigned, raw_res)
        assert raw_res == 15
        lltype.free(data, flavor='raw')

class Test_W_BoolType(BaseFFITest):
    def test_it_reads_a_bool_from_buffer(self, space):
        w_bool_type = ffitype.W_BoolType(space)
        bool_size = space.int_w(space.send(w_bool_type, 'size'))
        data = lltype.malloc(rffi.CCHARP.TO, bool_size, flavor='raw')
        misc.write_raw_unsigned_data(data, False, bool_size)
        w_res = w_bool_type.read(space, data)
        assert not space.is_true(w_res)
        lltype.free(data, flavor='raw')

    def test_it_writes_a_bool_to_buffer(self, space):
        w_bool_type = ffitype.W_BoolType(space)
        bool_size = space.int_w(space.send(w_bool_type, 'size'))
        data = lltype.malloc(rffi.CCHARP.TO, bool_size, flavor='raw')
        w_true = space.execute("true")
        w_bool_type.write(space, data, w_true)
        raw_res = misc.read_raw_unsigned_data(data, bool_size)
        assert bool(raw_res)
        lltype.free(data, flavor='raw')

class Test_W_FloatType(BaseFFITest):
    def test_it_reads_a_float32_to_buffer(self, space):
        w_float32_type = ffitype.W_FloatType(space, ffitype.FLOAT32)
        data = lltype.malloc(rffi.CCHARP.TO, 4, flavor='raw')
        misc.write_raw_float_data(data, 1.25, 4)
        w_res = w_float32_type.read(space, data)
        assert self.unwrap(space, w_res) == 1.25
        lltype.free(data, flavor='raw')

    def test_it_reads_a_float64_to_buffer(self, space):
        w_float64_type = ffitype.W_FloatType(space, ffitype.FLOAT64)
        data = lltype.malloc(rffi.CCHARP.TO, 8, flavor='raw')
        misc.write_raw_float_data(data, 1e-10, 8)
        w_res = w_float64_type.read(space, data)
        assert self.unwrap(space, w_res) == 1e-10
        lltype.free(data, flavor='raw')

    def test_it_writes_a_float32_to_buffer(self, space):
        w_float32_type = ffitype.W_FloatType(space, ffitype.FLOAT32)
        data = lltype.malloc(rffi.CCHARP.TO, 4, flavor='raw')
        w_f = space.newfloat(3.75)
        w_float32_type.write(space, data, w_f)
        raw_res = misc.read_raw_float_data(data, 4)
        assert raw_res == 3.75
        lltype.free(data, flavor='raw')

    def test_it_writes_a_float64_to_buffer(self, space):
        w_float64_type = ffitype.W_FloatType(space, ffitype.FLOAT64)
        data = lltype.malloc(rffi.CCHARP.TO, 8, flavor='raw')
        w_f = space.newfloat(1e-12)
        w_float64_type.write(space, data, w_f)
        raw_res = misc.read_raw_float_data(data, 8)
        assert raw_res == 1e-12
        lltype.free(data, flavor='raw')

class TestFFI__Type__MappedObject(BaseFFITest):
    def test_its_superclass_is_Type(self, space):
        assert self.ask(space, "FFI::Type::Mapped.superclass.equal? FFI::Type")

class TestFFI__Type__MappedObject__new(BaseFFITest):
    def test_it_takes_a_data_converter_as_argument(self, space):
        with self.raises(space, "NoMethodError",
                         "native_type method not implemented"):
            space.execute("FFI::Type::Mapped.new(0)")
        with self.raises(space, "NoMethodError",
                         "to_native method not implemented"):
            space.execute("""
            class DataConverter
              def native_type; nil; end
            end
            FFI::Type::Mapped.new(DataConverter.new)
            """)
        with self.raises(space, "NoMethodError",
                         "from_native method not implemented"):
            space.execute("""
            class DataConverter
              def native_type; nil; end
              def to_native; nil; end
            end
            FFI::Type::Mapped.new(DataConverter.new)
            """)
        w_res = space.execute("""
        class DataConverter
          def native_type; FFI::Type::VOID; end
          def to_native; nil; end
          def from_native; nil; end
        end
        FFI::Type::Mapped.new(DataConverter.new)
        """)
        assert space.getclass(w_res.w_data_converter).name == 'DataConverter'

    def test_it_derives_the_typeindex_from_the_data_converter(self, space):
        w_res = space.execute("""
        class DataConverter
          def native_type
            FFI::Type::UINT16
          end
          def to_native; nil; end
          def from_native; nil; end
        end
        FFI::Type::Mapped.new(DataConverter.new)
        """)
        assert type_names[w_res.typeindex] == "UINT16"
        with self.raises(space, "TypeError",
                         "native_type did not return instance of FFI::Type"):
            space.execute("""
            class DataConverter
              def native_type; nil; end
              def to_native; nil; end
              def from_native; nil; end
            end
            FFI::Type::Mapped.new(DataConverter.new)
            """)

class TestFFI__Type__MappedObject_to_native(BaseFFITest):
    def test_it_delegates_to_the_data_converter(self, space):
        w_res = space.execute("""
        class DataConverter
          def native_type; FFI::Type::VOID; end
          def to_native; :success; end
          def from_native; nil; end
        end
        mapped = FFI::Type::Mapped.new(DataConverter.new)
        mapped.to_native
        """)
        assert self.unwrap(space, w_res) == 'success'

class TestFFI__Type__MappedObject_from_native(BaseFFITest):
    def test_it_delegates_from_the_data_converter(self, space):
        w_res = space.execute("""
        class DataConverter
          def native_type; FFI::Type::VOID; end
          def to_native; nil; end
          def from_native; :success; end
        end
        mapped = FFI::Type::Mapped.new(DataConverter.new)
        mapped.from_native
        """)
        assert self.unwrap(space, w_res) == 'success'
