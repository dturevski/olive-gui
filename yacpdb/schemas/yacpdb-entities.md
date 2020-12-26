# The YACPDB entities format

## Overview

An entity is something a chess composition can have a reference to. For example, a composition can reference a
certain person as one of it authors or a certain magazine as a place of its original publication.
There are currently 3 supported types of entities: **persons**, **sources** & **tourneys** (that is composing
tourneys, solving tourneys are actually sources).

The candidate for the fourth type of entity is **keyword**.

Just like the compositions, the entities are manipulated as [YAML](http://en.wikipedia.org/wiki/YAML)
wiki-documents. The
formal [JSON schema](https://json-schema.org/)s for each of the entity types can be found here:

* [yacpdb-person.schema.json](yacpdb-person.schema.json)
* [yacpdb-source.schema.json](yacpdb-source.schema.json)
* [yacpdb-tourney.schema.json](yacpdb-tourney.schema.json)

Below is informal documentation-by-example.

## Person
A composition can reference a **person** as an author or as a judge (who awarded the distinction).
```yaml
familyname: Петков
givennames: Петко Андонов
foreignids:
  - domain: database.wfcc.ch
    id: 116786
comments:
  - A Grandmaster of Chess Composition, has 666 (or pretty close) FIDE Album points, which is an absolute record
```
The only required field is `familyname`, `givennames` is optional, note, that the latter is not a list.
The only possible value for `foreignids.domain` at the moment is **database.wfcc.ch**.
`foreignids.id` is an integer, it can be found, for example, by clicking the "Export XML" button at the
[composers's page](https://database.wfcc.ch/index.php?-table=composers&-action=browse&-recordid=composers%3Fid%3D116786).

**There is no point in copying the information from the WFCC database into the YACPDB comments.**
As long as we have the correct id, it can be fetched automatically and kept up-to-date.

## Source
A composition can reference a **source** as a place of the original publication or of a reprint.
```yaml
name: feenschach
type: magazine
foreignids:
  - domain: database.wfcc.ch
    id: 255
comments:
  - I should have a meaningful comment here, but I don't
```
The only required field is `name`. All comments regarding the `foreignids` above apply to the sources as well.

Possible values for `type` are:
* magazine
* newspaper
* booklet
* award booklet
* book
* anthology
* article
* lecture
* solving event
* website

## Tourney
This is for composing tourneys. Solving tourneys are sources with type "solving event".
```yaml
name: SuperProblem TT-420
comments:
  - This could be a good place to copy the tourney theme of the thematic tourney
  - A link to the award maybe
```
The only required field is `name`. 