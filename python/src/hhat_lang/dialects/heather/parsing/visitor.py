from __future__ import annotations

from arpeggio import NonTerminal, PTNodeVisitor, SemanticActionResults

from hhat_lang.core.code.ast import AST
from hhat_lang.dialects.heather.code.ast import (
    ArgTypePair,
    ArgValuePair,
    CompositeId,
    EnumTypeMember,
<<<<<<< HEAD
    FnArgs,
    FnDef,
=======
>>>>>>> upstream/main
    Id,
    Imports,
    Main,
    Program,
    SingleTypeMember,
    TypeDef,
    TypeImport,
    TypeMember,
)


class ParserVisitor(PTNodeVisitor):
    def visit_program(self, node: NonTerminal, child: SemanticActionResults) -> AST:
<<<<<<< HEAD
        """
        Construct a Program AST node from parsed children.

        Flattens any nested tuples in children to ensure all AST nodes
        are directly accessible at the Program level.

        Args:
            node: The parse tree node (unused)
            child: Semantic action results containing parsed children

        Returns:
            Program AST node with flattened children
        """
        # Flatten any tuples in children so all AST nodes are directly accessible
        flat_children = []
        for c in child:
            if isinstance(c, tuple):
                flat_children.extend(c)
            else:
                flat_children.append(c)

        prog = Program(main=None, imports=None)
        prog._value = tuple(flat_children)
        return prog

    def visit_fns(self, node: NonTerminal, child: SemanticActionResults) -> FnDef:
        """
        Construct a FnDef AST node from parsed function definition components.

        Handles the Heather function syntax: fn name(args) type {body}
        where type and body may be optional depending on the grammar.

        Args:
            node: The parse tree node (unused)
            child: Semantic action results containing [fn_name, fn_args, fn_type?, fn_body?]

        Returns:
            FnDef AST node representing the function definition
        """
        # child: [fn_name, fn_args, fn_type?, fn_body?]
        # Some elements may be missing (e.g., fn_type)
        fn_name = child[0]
        if not isinstance(fn_name, Id):
            fn_name = Id(str(fn_name))

        fn_args = child[1] if len(child) > 1 else FnArgs()

        fn_type = child[2] if len(child) > 2 else None
        if fn_type is not None and not isinstance(fn_type, Id):
            fn_type = Id(str(fn_type))

        fn_body = child[3] if len(child) > 3 else None

        return FnDef(fn_name, fn_type, fn_args, fn_body)
=======
        raise NotImplementedError()
>>>>>>> upstream/main
