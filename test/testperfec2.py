import unittest
from undecorated import undecorated
from unittest import mock
from unittest.mock import Mock, PropertyMock, call

import perfec2

test_lines = [
    'package com.coxautoinc.acctmgmt.person.controller;\n,'
    '\n,'
    'import com.coxautoinc.acctmgmt.assemblers.AMSPagedResourcesAssembler;\n,'
    'import com.coxautoinc.acctmgmt.assemblers.ContactAssembler;\n,'
    'import com.coxautoinc.acctmgmt.context.ContextAware;\n,'
    'import com.coxautoinc.acctmgmt.controller.PersonApplicationController;\n,'
    'import com.coxautoinc.acctmgmt.entities.Contact;\n,'
    'import com.coxautoinc.acctmgmt.entities.Person;\n,'
    'import com.coxautoinc.acctmgmt.exception.ResourceNotFoundException;\n,'
    'import com.coxautoinc.acctmgmt.person.service.PersonContactService;\n,'
    'import com.coxautoinc.acctmgmt.repositories.ContactRepository;\n,'
    'import com.coxautoinc.acctmgmt.resources.ContactResource;\n,'
    'import com.coxautoinc.acctmgmt.util.ErrorResponseBuilder;\n,'
    'import com.fasterxml.jackson.core.JsonProcessingException;\n,'
    'import lombok.extern.slf4j.Slf4j;\n,'
    'import org.springframework.beans.factory.annotation.Autowired;\n,'
    'import org.springframework.data.domain.Page;\n,'
    'import org.springframework.data.domain.Pageable;\n,'
    'import org.springframework.data.web.PagedResourcesAssembler;\n,'
    'import org.springframework.http.HttpStatus;\n,'
    'import org.springframework.http.MediaType;\n,'
    'import org.springframework.http.ResponseEntity;\n,'
    'import org.springframework.stereotype.Controller;\n,'
    'import org.springframework.validation.BindingResult;\n,'
    'import org.springframework.web.bind.annotation.*;\n,'
    '\n,'
    'import javax.validation.Valid;\n,'
    'import java.util.Optional;\n,'
    'import java.util.UUID;\n,'
    '\n,'
    '@Slf4j\n,'
    '@Controller\n,'
    '@RequestMapping(value = "/person", produces = MediaType.APPLICATION_JSON_VALUE)\n,'
    'public class PersonContactController extends PersonApplicationController {\n,'
    '\n,'
    '    @Autowired\n,'
    '    private PersonContactService personContactService;\n,'
    '\n,'
    '    @Autowired\n,'
    '    private ContactRepository contactRepository;\n,'
    '\n,'
    '    @Autowired\n,'
    '    AMSPagedResourcesAssembler amsAssembler;\n,'
    '\n,'
    '    @Autowired\n,'
    '    private ContactAssembler contactAssembler;\n,'
    '\n,'
    '    @PostMapping(value = "/uid/{personUid}/contactType/uid/{contactTypeUid}/contact")\n,'
    '    @ResponseBody\n,'
    '    public ResponseEntity<String> createContactAndAssociate(@PathVariable("personUid") UUID personUid,\n,'
    '                                                            @PathVariable("contactTypeUid") UUID contactTypeUid,\n,'
    '                                                            @Valid @RequestBody ContactResource contactResource,\n,'
    '                                                            BindingResult bindingResult) throws JsonProcessingException {\n,'
    '        log.info("Start createContactAndAssociate for CorrelationId: {}.  Person Uid: {}, ContactType Uid : {}",\n,'
    '                ContextAware.getAppContext().getCorrelationId(), personUid, contactTypeUid);\n,'
    '\n,'
    '        final ErrorResponseBuilder errorResponseBuilder = fromBindingResult(bindingResult,mapper);\n,'
    '        if(errorResponseBuilder.hasErrors()){\n,'
    '            return toResponseEntity(errorResponseBuilder.build(), HttpStatus.BAD_REQUEST);\n,'
    '        }\n,'
    '        final Contact contactResourceResp = personContactService.createContactForForPerson(personUid, contactTypeUid, contactResource);\n,'
    '        return toResponseEntity(contactResourceResp,HttpStatus.CREATED, contactAssembler);\n,'
    '    }\n,'
    '\n,'
    '    @PostMapping(value = "/uid/{personUid}/contactType/key/{contactTypeKey}/contact")\n,'
    '    @ResponseBody\n,'
    '    public ResponseEntity<String> createContactForKeyAndAssociateToPerson(@PathVariable("personUid") UUID personUid,\n,'
    '                                                                          @PathVariable("contactTypeKey") String contactTypeKey,\n,'
    '                                                                          @Valid @RequestBody ContactResource contactResource,\n,'
    '                                                                          BindingResult bindingResult) throws JsonProcessingException {\n,'
    '        log.info("Start createContactForKeyAndAssociateToPerson for CorrelationId: {}.  Person Uid: {}, ContactType Key : {}",\n,'
    '                ContextAware.getAppContext().getCorrelationId(), personUid, contactTypeKey);\n,'
    '\n,'
    '        final ErrorResponseBuilder errorResponseBuilder = fromBindingResult(bindingResult,mapper);\n,'
    '        if(errorResponseBuilder.hasErrors()){\n,'
    '            return toResponseEntity(errorResponseBuilder.build(), HttpStatus.BAD_REQUEST);\n,'
    '        }\n,'
    '\n,'
    '        final Contact contactResourceResp = personContactService.createContactForForPerson(personUid, contactTypeKey, contactResource);\n,'
    '        return toResponseEntity(contactResourceResp,HttpStatus.CREATED, contactAssembler);\n,'
    '    }\n,'
    '\n,'
    '    @RequestMapping(value = "/uid/{personUid}/contact/uid/{contactUid}", method = RequestMethod.GET)\n,'
    '    @ResponseBody\n,'
    '    public ResponseEntity<String> retrieveAssociatedContact(@PathVariable("personUid") UUID personUid, @PathVariable("contactUid") UUID contactUid) throws JsonProcessingException {\n,'
    '        log.info("Start retrieveAssociatedContact for CorrelationId : {}, personUid : {}, contactUid : {}",\n,'
    '                ContextAware.getAppContext().getCorrelationId(), personUid, contactUid);\n,'
    '        getPerson(personUid);\n,'
    '        final Contact contact = getContact(contactUid);\n,'
    '\n,'
    '        if (!personContactService.existsPersonAndContactRelation(personUid, contact)) {\n,'
    '            throw new ResourceNotFoundException(String.format("Person {%s} and contact {%s} are not associated", personUid, contactUid));\n,'
    '        }\n,'
    '\n,'
    '        return toResponseEntity(contact, HttpStatus.OK, contactAssembler);\n,'
    '    }\n,'
    '\n,'
    '    @RequestMapping(value = "/uid/{personUid}/contact/uid/{contactUid}", method = RequestMethod.PUT)\n,'
    '    @ResponseBody\n,'
    '    public ResponseEntity<String> updateContactPersonAssociation(@PathVariable("personUid") UUID personUid, @PathVariable("contactUid") UUID contactUid) throws JsonProcessingException {\n,'
    '        log.info("Start updateContactPersonAssociation for CorrelationId : {}, personUid : {}, contactUid : {}",\n,'
    '                ContextAware.getAppContext().getCorrelationId(), personUid, contactUid);\n,'
    '        final Person person = getPerson(personUid);\n,'
    '        final Contact contact = getContact(contactUid);\n,'
    '\n,'
    '        if (!personContactService.existsPersonAndContactRelation(personUid, contact)) {\n,'
    '            contact.associate(person);\n,'
    '            contactRepository.save(contact);\n,'
    '        }\n,'
    '\n,'
    '        return toResponseEntity(contact, HttpStatus.OK, contactAssembler);\n,'
    '    }\n,'
    '\n,'
    '    @RequestMapping(value = "/uid/{personUid}/contact/uid/{contactUid}", method = RequestMethod.DELETE)\n,'
    '    @ResponseBody\n,'
    '    public ResponseEntity<String> deleteContactPersonAssociation(@PathVariable("personUid") UUID personUid, @PathVariable("contactUid") UUID contactUid) throws JsonProcessingException {\n,'
    '        log.info("Start deleteContactPersonAssociation for CorrelationId : {}, personUid : {}, contactUid : {}",\n,'
    '                ContextAware.getAppContext().getCorrelationId(), personUid, contactUid);\n,'
    '        final Person person = getPerson(personUid);\n,'
    '        final Contact contact = getContact(contactUid);\n,'
    '\n,'
    '        if (!personContactService.existsPersonAndContactRelation(personUid, contact)) {\n,'
    '            throw new ResourceNotFoundException(String.format("Person {%s} and contact {%s} are not associated", personUid, contactUid));\n,'
    '        }\n,'
    '\n,'
    '        contact.disassociate(person);\n,'
    '        contactRepository.save(contact);\n,'
    '\n,'
    '        return new ResponseEntity<>(HttpStatus.NO_CONTENT);\n,'
    '    }\n,'
    '\n,'
    '    @RequestMapping(value = "/uid/{personUid}/contact/all", method = RequestMethod.GET)\n,'
    '    @ResponseBody\n,'
    '    public ResponseEntity<String> retrieveAllAssociatedContacts(@PathVariable("personUid") UUID personUid, Pageable pageable, PagedResourcesAssembler<ContactResource> pagedResourcesAssembler) throws JsonProcessingException {\n,'
    '        log.info("Start retrieveAllAssociatedContacts for CorrelationId : {}, personUid : {}",\n,'
    '                ContextAware.getAppContext().getCorrelationId(), personUid);\n,'
    '        final Person person = getPerson(personUid);\n,'
    '        Page<Contact> requests = fetchAllAssociatedContacts(pageable, person);\n,'
    '        return toResponseEntity(requests, HttpStatus.OK, pageable, pagedResourcesAssembler, contactAssembler);\n,'
    '    }\n,'
    '\n,'
    '    private Contact getContact(UUID contactUid) {\n,'
    '        Optional<Contact> contact = contactRepository.findById(contactUid);\n,'
    '\n,'
    '        if (!contact.isPresent()) {\n,'
    '            throw new ResourceNotFoundException(String.format("Contact {%s} was not found", contactUid));\n,'
    '        }\n,'
    '\n,'
    '        return contact.get();\n,'
    '    }\n,'
    '\n,'
    '    protected Page<Contact> fetchAllAssociatedContacts(Pageable pageable, Person person) {\n,'
    '        Page<Contact> page = contactRepository.findAllByPeopleEquals(pageable, person);\n,'
    '\n,'
    '        if (page == null) {\n,'
    '            throw new ResourceNotFoundException(String.format("Error retrieving associations for person {%s}", person.getUid()));\n,'
    '        } else if (page.getTotalElements() == 0L){\n,'
    '            throw new ResourceNotFoundException(String.format("Person {%s} has no associated contacts", person.getUid()));\n,'
    '        }\n,'
    '\n,'
    '        return page;\n,'
    '    }\n,'
    '}\n,'
]


class Test_add_field_annotation(unittest.TestCase):

    def setUp(self) -> None:
        self.testee = undecorated(perfec2.add_field_annotation)

    @mock.patch('perfec2.util.annotation_with_props_lines')
    @mock.patch('perfec2.util.match_indentation_and_insert')
    def test_no_properties(self, match_indentation_and_insert, annotation_with_props_lines):
        field = Mock()
        position = PropertyMock()
        line = PropertyMock(return_value=1)
        type(field).position = position
        type(position).line = line

        props = None
        lines = [
            'one\n',
            '    private String two;\n',
            '    three\n',
            'four\n'
        ]
        anno = 'hello'

        annotation_with_props_lines.return_value = ['doesnt matter, arg for match_indentation_and_insert']
        match_indentation_and_insert.return_value = [
            'one\n',
            '\n',
            '    @hello\n',
            '    private String two;\n',
            '\n',
            '    three\n',
            'four\n'
        ]

        actual = self.testee(field, anno, lines, props)
        self.assertEqual(match_indentation_and_insert.return_value, actual)

        annotation_with_props_lines.assert_not_called()
        match_indentation_and_insert.assert_called_once()

    @mock.patch('perfec2.util.annotation_with_props_lines')
    @mock.patch('perfec2.util.match_indentation_and_insert')
    def test_with_properties(self, match_indentation_and_insert, annotation_with_props_lines):
        field = Mock()
        position = PropertyMock()
        line = PropertyMock(return_value=1)
        type(field).position = position
        type(position).line = line

        props = {
            'some': '""',
            'annotation': '"properties"',
            'sldfk': 777,
        }
        lines = [
            'one\n',
            '    private String two;\n',
            '    three\n',
            'four\n'
        ]
        anno = 'hello'

        annotation_with_props_lines.return_value = ['doesnt matter, arg for match_indentation_and_insert']
        match_indentation_and_insert.return_value = [
            'one\n',
            '\n',
            '    @hello(\n',
            '        some=""\n',
            '        annotation="properties"\n',
            '        sldfk=777'
            '    )\n',
            '    private String two;\n',
            '\n',
            '    three\n',
            'four\n'
        ]

        actual = self.testee(field, anno, lines, props)
        self.assertEqual(match_indentation_and_insert.return_value, actual)

        annotation_with_props_lines.assert_called_with(anno, props)
        match_indentation_and_insert.assert_called_once()
        # # match_indentation_and_insert.assert_called_with( # fixme ????
        #     annotation_with_props_lines.return_value, field.position.line.return_value, lines, pos='above')


class Test_field_height(unittest.TestCase):
    # todo
    pass

class Test_field_spacing(unittest.TestCase):

    def setUp(self) -> None:
        self.testee = undecorated(perfec2.field_spacing)

    @mock.patch('perfec2.util._add_newline_if_not_empty')
    @mock.patch('perfec2.util.field_height')
    def test_no_surrounding_spaces(self, field_height, _add_newline_if_not_empty):
        field = Mock()
        position = PropertyMock()
        line = PropertyMock(return_value=1)
        type(field).position = position
        type(position).line = line

        lines = ['public class One {\n', '   private String two;\n', '   public List<> three;\n', '\n']

        field_height.return_value = 999  # doesnt matter
        add_newline_retvals = [
            ['public class One {\n', '   private String two;\n', '\n', '   public List<> three;\n', '\n'],
            ['public class One {\n', '\n', '   private String two;\n', '\n', '   public List<> three;\n', '\n'],
        ]
        _add_newline_if_not_empty.side_effect = add_newline_retvals

        actual = self.testee(field, lines)
        add_newline_calls = [
            call(field.position.line - 1, lines, pos='bottom'),
            call(field.position.line - 1 - field_height.return_value, add_newline_retvals[0])
        ]
        _add_newline_if_not_empty.assert_has_calls(add_newline_calls)
        self.assertEqual(
            ['public class One {\n', '\n', '   private String two;\n', '\n', '   public List<> three;\n', '\n'],
            actual)

    @mock.patch('perfec2.util._add_newline_if_not_empty')
    @mock.patch('perfec2.util.field_height')
    def test_bottom_space(self, field_height, _add_newline_if_not_empty):
        field = Mock()
        position = PropertyMock()
        line = PropertyMock(return_value=1)
        type(field).position = position
        type(position).line = line

        lines = ['public class One {\n', '   private String two;\n', '\n', '   public List<> three;\n', '\n']

        field_height.return_value = 999  # doesnt matter
        add_newlines_retvals = [
            lines,
            ['public class One {\n', '\n', '   private String two;\n', '\n', '   public List<> three;\n', '\n'],
        ]
        _add_newline_if_not_empty.side_effect = add_newlines_retvals

        actual = self.testee(field, lines)
        _add_newline_if_not_empty.assert_has_calls([
            call(field.position.line - 1, lines, pos='bottom'),
            call(field.position.line - 1 - field_height.return_value, add_newlines_retvals[0])
        ])
        self.assertEqual(add_newlines_retvals[1], actual)

    @mock.patch('perfec2.util._add_newline_if_not_empty')
    @mock.patch('perfec2.util.field_height')
    def test_top_space(self, field_height, _add_newline_if_not_empty):
        field = Mock()
        position = PropertyMock()
        line = PropertyMock(return_value=1)
        type(field).position = position
        type(position).line = line

        lines = ['public class One {\n', '\n', '   private String two;\n', '   public List<> three;\n', '\n']

        field_height.return_value = 999  # doesnt matter
        add_newlines_retvals = [
            ['public class One {\n', '\n', '   private String two;\n', '\n', '   public List<> three;\n', '\n'],
            ['public class One {\n', '\n', '   private String two;\n', '\n', '   public List<> three;\n', '\n'],
        ]
        _add_newline_if_not_empty.side_effect = add_newlines_retvals

        actual = self.testee(field, lines)
        _add_newline_if_not_empty.assert_has_calls([
                call(field.position.line - 1, lines, pos='bottom'),
                call(field.position.line - 1 - field_height.return_value, add_newlines_retvals[0])
        ])
        self.assertEqual(add_newlines_retvals[1], actual)

    @mock.patch('perfec2.util._add_newline_if_not_empty')
    @mock.patch('perfec2.util.field_height')
    def test_surrounding_spaces(self, field_height, _add_newline_if_not_empty):
        field = Mock()
        position = PropertyMock()
        line = PropertyMock(return_value=1)
        type(field).position = position
        type(position).line = line

        lines = ['public class One {\n', '\n', '   private String two;\n', '\n', '   public List<> three;\n', '\n']

        field_height.return_value = 999  # doesnt matter
        add_newlines_retvals = [
            ['public class One {\n', '\n', '   private String two;\n', '\n', '   public List<> three;\n', '\n'],
            ['public class One {\n', '\n', '   private String two;\n', '\n', '   public List<> three;\n', '\n'],
        ]
        _add_newline_if_not_empty.side_effect = add_newlines_retvals

        actual = self.testee(field, lines)
        _add_newline_if_not_empty.assert_has_calls([
            call(field.position.line - 1, lines, pos='bottom'),
            call(field.position.line - 1 - field_height.return_value, add_newlines_retvals[0])
        ])
        self.assertEqual(add_newlines_retvals[1], actual)

    @mock.patch('perfec2.util._add_newline_if_not_empty')
    @mock.patch('perfec2.util.field_height')
    def test_existing_annotation(self, field_height, _add_newline_if_not_empty):
        field = Mock()
        position = PropertyMock()
        line = PropertyMock(return_value=1)
        type(field).position = position
        type(position).line = line

        lines = ['public class One {\n', '@MyAnnotation\n', '   private String two;\n', '   public List<> three;\n', '\n']

        field_height.return_value = 999  # doesnt matter
        add_newlines_retvals = [
            ['public class One {\n', '@MyAnnotation\n', '   private String two;\n', '\n', '   public List<> three;\n', '\n'],
            ['public class One {\n', '\n', '@MyAnnotation\n', '   private String two;\n', '\n', '   public List<> three;\n', '\n'],
        ]
        _add_newline_if_not_empty.side_effect = add_newlines_retvals

        actual = self.testee(field, lines)
        _add_newline_if_not_empty.assert_has_calls([
            call(field.position.line - 1, lines, pos='bottom'),
            call(field.position.line - 1 - field_height.return_value, add_newlines_retvals[0])
        ])
        self.assertEqual(add_newlines_retvals[1], actual)

    def test_existing_annotations(self, util):
        # todo
        pass

    def test_existing_multiline_annotation(self, util):
        # todo
        pass


# fixme move into main module tests module
class TestFindTestee(unittest.TestCase):

    def setUp(self) -> None:
        self.testee = undecorated(perfec2.find_testee)

    @mock.patch('perfec2.util')
    def test_happy(self, util):
        clazz = Mock()
        fields = PropertyMock()
        decl_name = PropertyMock()
        clazz_name = PropertyMock()

        declr = Mock()
        type(declr).name = decl_name

        type(clazz).name = clazz_name
        type(clazz).fields = fields
        type(clazz).declarators = [declr]

        util.field_has_name.side_effect = [False, False, True]
        util.field_has_anno.side_effect = [False, False, False]

        type(clazz).fields = fields

# mock a dependency method call

# @mock.patch.object(RemovalService, 'rm')
# def test_upload_complete(self, mock_rm):


# mock.create_autospec(RemovalService) what about with req. constructor args?

# class ExampleTest(unittest.TestCase):
#
#     @mock.patch('testee_module.dependency_module2')
#     @mock.patch('testee_module.dependency_module1')
#     @mock.patch.object(DependencyClass, 'class_method_name')
#     def testmethod(self, dependency_module1, dependency_module2):
#
#         dependency_module1.method_called_by_testee.return_value = 'desired return value'
#
#         testmethod()
#
#         self.assertFalse(dependency1.method_called_by_testee.called, "Method wasnt called")
#
#         # verify dependency method was called with certain args
#         dependency1.method_called_by_testee.assert_called_with('args that should have been used')
#


# #!/usr/bin/env python
# # -*- coding: utf-8 -*-
#
# import os
# import os.path
#
# def rm(filename):
#     if os.path.isfile(filename):
#         os.remove(filename)

# from mymodule import rm
#
# import mock
# import unittest
#
#
# class RmTestCase(unittest.TestCase):
#
#     @mock.patch('mymodule.os.path')
#     @mock.patch('mymodule.os')
#     def test_rm(self, mock_os, mock_path):
#         # set up the mock
#         mock_path.isfile.return_value = False
#
#         rm("any path")
#
#         # test that the remove call was NOT called.
#         self.assertFalse(mock_os.remove.called, "Failed to not remove the file if not present.")
#
#         # make the file 'exist'
#         mock_path.isfile.return_value = True
#
#         rm("any path")
#
#         mock_os.remove.assert_called_with("any path")
