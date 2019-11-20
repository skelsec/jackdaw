const PrimitiveService = require('../client/Services/PrimitiveService');

var unit = {
    "primitive": "block",
    "title": "Root",
    "properties": {
        "name": "Root",
        "fuzzable": true
    },
    "children": [
        {
            "primitive": "block",
            "title": "TestBlock1",
            "properties": {
                "name": "TestBlock1",
                "logic": "linear",
                "fuzzable": true
            },
            "children": [
                {
                    "primitive": "binary",
                    "title": "TestBinary1",
                    "properties": {
                        "name": "TestBinary1",
                        "value": [
                            1,
                            1,
                            1,
                            1
                        ],
                        "fuzzable": false
                    },
                    "meta": {
                        "uuid": "188325a9-61ac-43ce-8eac-69bdcf5fe4bd"
                    }
                }
            ],
            "meta": {
                "uuid": "2ef97db8-312a-4da7-82a6-a63e8a33fa08"
            },
            "expanded": true
        },
        {
            "primitive": "block",
            "title": "TestBlock2",
            "properties": {
                "name": "TestBlock2",
                "logic": "linear",
                "fuzzable": true
            },
            "children": [
                {
                    "primitive": "block",
                    "title": "TestBlock3",
                    "properties": {
                        "name": "TestBlock3",
                        "logic": "linear",
                        "fuzzable": true
                    },
                    "children": [
                        {
                            "primitive": "word",
                            "title": "TestWord",
                            "properties": {
                                "name": "TestWord",
                                "value": [
                                    255,
                                    255
                                ],
                                "format": "binary",
                                "endian": "big",
                                "signed": false,
                                "full_range": false,
                                "fuzzable": true
                            },
                            "meta": {
                                "uuid": "dd547e9c-0a2b-4295-842c-f196dc38d38c"
                            }
                        }
                    ],
                    "meta": {
                        "uuid": "3728ed82-fb44-454c-ac35-ebf2ae7db4ca"
                    },
                    "expanded": true
                }
            ],
            "meta": {
                "uuid": "96e6bc42-12bf-490b-bf5d-43f0db4c5acc"
            },
            "expanded": true
        },
        {
            "primitive": "string",
            "title": "TestString",
            "properties": {
                "name": "TestString",
                "value": [
                    72,
                    101,
                    108,
                    108,
                    111
                ],
                "max_length": 0,
                "size": 0,
                "padding": 0,
                "ascii": true,
                "fuzzable": true
            },
            "meta": {
                "uuid": "ec8d7481-ce52-4bb5-8384-a0e845cf622b"
            }
        }
    ],
    "meta": {
        "uuid": "85ef0a94-57a5-4baa-90f4-550d714555e4"
    }
};

test('Recursive find primitive', () => {
    var primitiveUuid = 'deadbeef-dead-beef-dead-beefaaaaaaaa';
    var result = PrimitiveService.recursiveFindPrimitive(unit, primitiveUuid);
    expect(result).toBe(undefined);

    primitiveUuid = {};
    result = PrimitiveService.recursiveFindPrimitive(unit, primitiveUuid);
    expect(result).toBe(undefined);

    primitiveUuid = [];
    result = PrimitiveService.recursiveFindPrimitive(unit, primitiveUuid);
    expect(result).toBe(undefined);

    primitiveUuid = 1;
    result = PrimitiveService.recursiveFindPrimitive(unit, primitiveUuid);
    expect(result).toBe(undefined);

    primitiveUuid = 'ec8d7481-ce52-4bb5-8384-a0e845cf622b';
    result = PrimitiveService.recursiveFindPrimitive(unit, primitiveUuid);
    expect(result.meta.uuid).toBe(primitiveUuid);
    expect(result.primitive).toBe('string');
    expect(result.title).toBe('TestString');

    primitiveUuid = '188325a9-61ac-43ce-8eac-69bdcf5fe4bd';
    result = PrimitiveService.recursiveFindPrimitive(unit, primitiveUuid);
    expect(result.meta.uuid).toBe(primitiveUuid);
    expect(result.primitive).toBe('binary');
    expect(result.title).toBe('TestBinary1');

    primitiveUuid = 'dd547e9c-0a2b-4295-842c-f196dc38d38c';
    result = PrimitiveService.recursiveFindPrimitive(unit, primitiveUuid);
    expect(result.meta.uuid).toBe(primitiveUuid);
    expect(result.primitive).toBe('word');
    expect(result.title).toBe('TestWord');
});

test('Recursive find parent primitive', () => {
    var primitiveUuid = 'deadbeef-dead-beef-dead-beefaaaaaaaa';
    var result = PrimitiveService.recursiveFindPrimitive(unit, primitiveUuid);
    expect(result).toBe(undefined);

    primitiveUuid = {};
    result = PrimitiveService.recursiveFindPrimitive(unit, primitiveUuid);
    expect(result).toBe(undefined);

    primitiveUuid = [];
    result = PrimitiveService.recursiveFindPrimitive(unit, primitiveUuid);
    expect(result).toBe(undefined);

    primitiveUuid = 1;
    result = PrimitiveService.recursiveFindPrimitive(unit, primitiveUuid);
    expect(result).toBe(undefined);

    primitiveUuid = 'ec8d7481-ce52-4bb5-8384-a0e845cf622b';
    var parentUuid = '85ef0a94-57a5-4baa-90f4-550d714555e4';
    result = PrimitiveService.recursiveFindParentPrimitive(unit, primitiveUuid);
    expect(result.meta.uuid).toBe(parentUuid);
    expect(result.title).toBe('Root');

    primitiveUuid = 'dd547e9c-0a2b-4295-842c-f196dc38d38c';
    parentUuid = '3728ed82-fb44-454c-ac35-ebf2ae7db4ca';
    result = PrimitiveService.recursiveFindParentPrimitive(unit, primitiveUuid);
    expect(result.meta.uuid).toBe(parentUuid);

    primitiveUuid = '188325a9-61ac-43ce-8eac-69bdcf5fe4bd';
    parentUuid = '2ef97db8-312a-4da7-82a6-a63e8a33fa08';
    result = PrimitiveService.recursiveFindParentPrimitive(unit, primitiveUuid);
    expect(result.meta.uuid).toBe(parentUuid);
});

test('Recursive update primitive', () => {
    var targetState = JSON.parse(JSON.stringify(unit));
    var primitiveUuid = 'dd547e9c-0a2b-4295-842c-f196dc38d38c';
    var primitive = PrimitiveService.recursiveFindPrimitive(targetState, primitiveUuid);
    var newValue = JSON.parse(JSON.stringify(primitive));
    newValue.properties.value = [0, 0];
    PrimitiveService.recursiveUpdatePrimitive(targetState.children, newValue);
    var updatedPrimitive = PrimitiveService.recursiveFindPrimitive(targetState, primitiveUuid);
    expect(updatedPrimitive.properties.value).toEqual([0, 0]);
});

test('Recursive delete primitive', () => {
    var targetState = JSON.parse(JSON.stringify(unit));
    var primitiveUuid = 'dd547e9c-0a2b-4295-842c-f196dc38d38c';
    var primitive = PrimitiveService.recursiveFindPrimitive(targetState, primitiveUuid);
    expect(primitive.meta.uuid).toEqual(primitiveUuid);
    var result = PrimitiveService.recursiveDeletePrimitive(targetState.children, primitiveUuid);
    primitive = PrimitiveService.recursiveFindPrimitive(result, primitiveUuid);
    expect(primitive).toBe(null);
});
