# Columnar Data Model Direction

## Decision

Use NumPy-backed, typed column collections as the primary in-memory schema storage. Keep the existing object-based schema classes for scalar access and explicit object materialization.

For example, `SampleAnnotations` stores all annotation columns, while `SampleAnnotation` retains its current definition and represents one record. Apply the same collection/record separation to other schemas as they migrate.

The goals are lower per-record memory overhead and efficient bulk operations, while retaining convenient scalar APIs. Performance improvements must be measured; repeated scalar materialization can cost more than looking up an existing object.

This is a design direction, not an implemented API. The initial migration preserves the dataset JSON format and does not require Arrow as the storage backend. Extend columnar storage to derived domain data, including boxes, labels, shapes, and trajectories, so bulk processing stays array-based from schema loading through geometry and rendering. Existing scalar objects such as `Box3D` and `Quaternion` remain compatibility and explicit materialization boundaries.

## Collection model

The following sketch illustrates the proposed representation. Array aliases and helper types are illustrative; their final names can follow the repository's typing conventions.

```python
@define(frozen=True)
class SampleAnnotations:
    """Columnar annotation storage with N aligned rows."""

    token: NDArrayStr
    sample_token: NDArrayStr
    instance_token: NDArrayStr
    attribute_tokens: list[list[str]]
    visibility_token: NDArrayStr
    translation: NDArrayF64
    rotation: NDArrayF64
    size: NDArrayF64
    velocity: NDArrayF64
    acceleration: NDArrayF64
    num_lidar_pts: NDArrayI64
    num_radar_pts: NDArrayI64
    next: NDArrayStr
    prev: NDArrayStr
    automatic_annotation: NDArrayBool
    autolabel_metadata: list[list[AutolabelModel] | None]

    def by_token(self, token: str) -> SampleAnnotation: ...
    def row(self, index: int) -> SampleAnnotation: ...
    def take(self, indices: NDArrayI64) -> SampleAnnotations: ...
    def filter(self, mask: NDArrayBool) -> SampleAnnotations: ...
    def __len__(self) -> int: ...
```

Nested metadata and ragged attributes may remain Python lists initially. They retain some object overhead, but keep the first implementation small. A flat-values-plus-offsets representation can follow if profiling justifies it.

### Shapes and types

Every column must contain the same number of rows, `N`.

| Fields                       | Representation                          | Shape                            |
| ---------------------------- | --------------------------------------- | -------------------------------- |
| Tokens, `next`, `prev`       | String array                            | `(N,)`                           |
| Translation and size         | `float64` array                         | `(N, 3)`                         |
| Rotation                     | `float64` array, ordered `[w, x, y, z]` | `(N, 4)`                         |
| Velocity and acceleration    | Nullable `float64` vectors              | Values `(N, 3)`, validity `(N,)` |
| Lidar and radar point counts | `int64` array                           | `(N,)`                           |
| Automatic annotation flag    | Boolean array                           | `(N,)`                           |
| Attribute tokens             | List of lists of strings                | Outer length `N`                 |
| Autolabel metadata           | List of optional model lists            | Outer length `N`                 |

An empty collection retains these dtypes and dimensions, including `(0, 3)` and `(0, 4)` vector columns. For other schemas, timestamps retain their existing microsecond units in `int64` arrays.

String storage must preserve complete tokens and filenames. If fixed-width NumPy Unicode arrays are used, construction and replacement must size them correctly and never silently truncate values.

### Missing values

An optional array only describes an absent whole column; it cannot represent a mixture of present and missing row values. Use an explicit validity mask for nullable vectors:

- `valid[i] == True`: `values[i]` contains the record's vector.
- `valid[i] == False`: the record's value is `None`; the stored vector is ignored.
- A valid numerical `NaN` remains distinguishable from a missing value.

Selection must apply to both the values and validity mask. An entirely missing optional vector column is represented by an all-false mask.

## Access and ownership

### Bulk access

Expose arrays directly for vectorized operations:

```python
annotations = t4.sample_annotation
mask = annotations.num_lidar_pts > 0
centers = annotations.translation[mask]
selected = annotations.filter(mask)
```

`take()` and `filter()` return collections and select every field consistently, including nested lists and validity masks. `filter()` preserves source order; `take()` follows the supplied index order. For the initial token-addressable collection API, reject repeated indices in `take()` so the result retains unique tokens.

Share selection, length validation, and indexing mechanics across collections without obscuring schema-specific field types and validation.

### Scalar access

`row()` and `by_token()` materialize detached instances of the existing record class:

```python
record = annotations.by_token(token)  # SampleAnnotation
record.translation[0] = 1.0          # Does not update annotations
```

Materialization must:

- Convert rotation arrays to the existing `Quaternion` representation.
- Restore missing optional values to `None`.
- Copy mutable arrays, nested lists, and nested metadata objects so edits cannot affect collection storage.
- Populate derived shortcuts when dataset relationship context is available.

Repeated lookups need not return the same object. Avoid retaining a materialized object for every row, which would erase the memory benefit.

Each collection owns one token-to-row index. Unknown tokens raise `KeyError`. `T4Devkit.get_idx()` should delegate to this index, and `T4Devkit.get()` should delegate to scalar materialization in columnar mode.

### Mutation

Freeze new columnar schema dataclasses and their storage helper dataclasses using `@define(frozen=True)`. Preventing field reassignment protects row alignment and token-index consistency. Start with read-only columns and explicit replacement operations that return new collections.

A frozen dataclass alone is insufficient: NumPy arrays and nested Python lists can still be mutated. Owned arrays must be marked non-writeable, and nested storage must use immutable containers and frozen metadata or defensive access. List annotations in the sketch describe logical contents; they do not imply that mutable internal lists are exposed.

Keep existing detached scalar schema records mutable during migration for compatibility. Freezing those public record classes is a separate breaking change: callers must replace records explicitly, and derived shortcuts must be supplied at construction rather than assigned afterward.

Construction must establish ownership of input buffers and nested values. Array exposure should be read-only; nested list exposure must use defensive copies or immutable views. The sketch describes field contents, not permission to mutate internal containers.

Do not support implicit write-through from scalar objects. Future batch editing should produce a new collection or dataset snapshot, validate it, and rebuild affected token and relationship indexes. The exact editing API is deferred.

## Columnar domain dataclasses

The direction covers `t4_devkit/dataclass` as well as schema records. Loading columnar annotations and immediately constructing a `list[Box3D]` for bulk processing would reintroduce per-object storage and computation overhead. Introduce frozen collection classes such as `Boxes3D` and `Boxes2D`, retaining `Box3D` and `Box2D` for detached scalar access during migration.

### Boxes and nested data

Each `Boxes3D` collection represents boxes at one timestamp in one coordinate frame. Store `unix_time: int` and `frame_id: str` once as frozen collection metadata; only per-box values have a leading dimension of `N`. Proposed fields are:

| Field           | Representation                                                                  |
| --------------- | ------------------------------------------------------------------------------- |
| `unix_time`     | Shared scalar `int`, in existing microsecond units                              |
| `frame_id`      | Shared scalar `str`                                                             |
| Semantic labels | Aligned label-name strings and immutable ragged attributes                      |
| `confidence`    | `float64`, `(N,)`                                                               |
| `uuid`          | Strings with a per-row validity mask                                            |
| `position`      | `float64`, `(N, 3)`                                                             |
| `rotation`      | `float64`, `(N, 4)`, `[w, x, y, z]`                                             |
| Shape           | Aligned shape types and sizes `(N, 3)`, with optional ragged footprint vertices |
| `velocity`      | Nullable vectors, values `(N, 3)`                                               |
| `num_points`    | `int64` with a per-row validity mask                                            |
| `visibility`    | Validated enum values, `(N,)`                                                   |
| `future`        | Aligned trajectory collection with per-box presence information                 |

Use typed nested column containers for labels, shapes, and trajectories where useful; do not store one `SemanticLabel`, `Shape`, or `Future` object per box in the primary numerical path. Preserve custom shape footprints and their geometry semantics rather than assuming every shape is a rectangular box. Construct Shapely objects only for scalar access or operations that need them.

`Boxes2D` follows the same shared timestamp and coordinate-frame contract, with nullable ROI values `(N, 4)` and nullable positions `(N, 3)`. Preserve the existing ROI coordinate convention. All selection operations must select nested columns and validity masks together.

`take()` and `filter()` preserve shared metadata, including when the result is empty. Scalar materialization supplies that metadata to each `Box3D` or `Box2D`. Construction from scalar boxes must reject mixed timestamps or frames; empty construction requires explicit metadata. Concatenation requires matching timestamps and frames. Represent multiple timestamps or frames as separate collections, grouped by `(unix_time, frame_id)`. This rule applies to box batches, not dataset schema tables whose timestamp columns can span many records, or future trajectories whose waypoints span time.

Box UUIDs are optional; uniqueness is not assumed without explicit validation. Use positional selection initially; any UUID lookup must return all matches or require an explicit disambiguating key.

### Batch geometry and immutability

New collection methods return new frozen collections instead of mutating inputs. Illustrative APIs are:

```python
boxes = t4.get_boxes3d(sample_data_token)  # Proposed batch API
corners = boxes.corners()                # (N, 8, 3)
moved = boxes.translated(offset)         # New Boxes3D
rotated = boxes.rotated(quaternion)      # New Boxes3D
transformed = boxes.transformed(transform)
box = transformed.row(0)                 # Detached Box3D
```

Define broadcasting explicitly: a shared translation `(3,)` or one per row `(N, 3)`, and a shared rotation `(4,)` or one per row `(N, 4)`. These geometry edits preserve the shared timestamp and frame ID. A coordinate-frame transform validates its source against the collection's `frame_id`, applies to the entire batch, and returns a collection with the destination `frame_id` and unchanged `unix_time`. It does not perform temporal interpolation. Mixed-frame inputs must be grouped into separate collections before transformation.

Preserve existing geometry conventions: size is `[width, length, height]`, quaternion composition order matches scalar behavior, and corner ordering is unchanged. Translation affects positions and future waypoints; rotation also affects orientations and valid velocities. A coordinate-frame transform applies these operations consistently to nested trajectories. Keep shape dimensions unchanged by rigid transforms.

Current `Box3D.translate()`, `rotate()`, and `with_future()`, and `Box2D.with_position()`, mutate their objects. Retain those scalar semantics during compatibility migration; give new batch operations explicit return-new-value semantics and update callers to use the returned result.

### Trajectories, transforms, and point clouds

- **Trajectories:** `ObjectPath` already contains arrays for one object's path. Extend to batches using dense `(N, M, T, D)` waypoints where mode and horizon dimensions are shared, with aligned timestamps, confidences, and validity information. For variable lengths, use offsets and flat buffers or a documented padded representation with masks. Distinguish an absent future from a present empty trajectory and preserve each object's timestamps. Choose the initial ragged layout after inspecting real workloads.
- **Transforms:** Keep a single `HomogeneousMatrix` as a useful scalar value and add batch application. Introduce aligned `(N, 4, 4)` transform storage only where collections of transforms are needed. `TransformBuffer` remains a lookup service, rather than becoming a table solely because it is implemented as a dataclass.
- **Point clouds:** `PointCloud.points` is already array-backed. Preserve this representation initially and align its mutation policy with new immutable batch APIs as consumers migrate. A collection of scans can use point offsets plus scan-level metadata if required; do not add another batch axis without a use case.

The collection/record distinction is based on what the data represents: repeated domain entities get aligned columns, while individual values and lookup services retain appropriate scalar or service interfaces. New columnar domain containers follow the same frozen-field, read-only-buffer, and detached-scalar contracts as schema collections.

## Relationships and derived fields

Separate stored schema fields from dataset-level relationship indexes. Replace the record mutation currently performed by `T4Devkit.__make_reverse_index__` with indexes or derived arrays for:

- Annotation category names through instance/category relationships.
- Sample-data channel and modality through calibrated sensors and sensors.
- Sample-to-annotation relationships and sample/channel-to-sample-data lookup.
- Sensor first sample-data tokens and log-to-map relationships.
- Timeseries lookups by sample/instance or sample-data/instance.

Keep a single owner for each index and reuse it across helpers. Preserve existing ordering and shortcut behavior during migration; changes to those semantics should be separate decisions.

Standalone collections can materialize records with the existing default shortcut values. Dataset-owned scalar access supplies resolved shortcuts. Selection must retain enough relationship context to resolve shortcuts correctly, rather than reusing stale positional indexes.

Derived fields are excluded from JSON serialization, matching the current treatment of `init=False` fields.

## Validation and serialization

Construction validates aligned lengths, shapes, dtypes, required fields, defaults, enum values, and existing schema constraints. Preserve autolabel consistency rules and nullable/default behavior. Do not rely on NumPy casting alone: it can accept or transform values that existing validators reject.

Maintain an explicit field specification for stored fields, defaults, nullability, and selection/serialization behavior. During transition, the existing record implementation and fixtures serve as a reference for validation parity.

Token-addressable collections require unique tokens. Reject duplicates with a clear diagnostic and document this as a behavior change from the current index comprehension, which retains the last duplicate. Other stricter validation changes should be considered separately.

Keep JSON as the authoritative dataset format initially:

- Add a columnar loader without changing the existing `build_schema()` return type immediately.
- Normalize JSON records directly into columns in the production loading path.
- Preserve empty strings, empty lists, null values, row order, and existing serialization defaults.
- Export stored fields through a dedicated collection serializer, excluding relationships and shortcuts.
- Preserve special schema cases, such as empty camera intrinsics for non-camera sensors.
- Keep raw-record sanity checking available so malformed inputs can be diagnosed before array conversion.

Round-trip compatibility means equivalent normalized JSON content, not identical whitespace or source formatting. Direct column construction avoids intermediate schema objects, but parsing a whole JSON array still has a peak-memory cost; streaming input is a separate optimization.

## Compatibility boundaries

Scalar results remain instances of the existing schema classes, so their methods and `attrs` serialization remain available. However, columnar storage changes several existing behaviors:

| Current behavior                                | Columnar direction                     |
| ----------------------------------------------- | -------------------------------------- |
| Tables are lists of record objects              | Tables are typed column collections    |
| `get()` returns a stored mutable object         | `get()` materializes a detached object |
| Repeated lookups share object identity          | Object identity is not guaranteed      |
| Record and list mutation can change stored data | Updates require explicit replacement   |
| Bulk work commonly iterates over records        | Bulk work operates on arrays           |

Keep the legacy object backend available during migration. An opt-in backend selector, such as `backend="columnar"`, allows callers to test these differences before the default changes. Do not silently return detached objects while implying that their mutation updates the dataset.

## Migration plan

1. **Establish behavior and performance baselines.** Capture load time, peak and retained memory, random and repeated token lookup latency, annotation filtering, relationship construction, and `get_box3ds()` performance. Cover defaults, nulls, ordering, category-index repair, validation, and normalized JSON export.
2. **Implement the annotation collection foundation.** Add `SampleAnnotations.from_records()`, nullable vectors, token indexing, scalar materialization, selection, and validation. Compare materialized records against the current implementation. Verify that modifying inputs or returned records cannot mutate storage.
3. **Add direct JSON-to-columns loading and export.** Avoid constructing all `SampleAnnotation` objects during normal loading. Retain the existing loader and add focused parity coverage for malformed inputs, empty collections, nested metadata, and ragged attributes.
4. **Integrate an opt-in columnar dataset backend.** Move relationship construction out of record mutation. Adapt `get()` and `get_idx()`, preserve scalar shortcuts, and migrate the remaining schema collections incrementally. Keep the legacy backend as a reference and fallback.
5. **Add columnar domain collections.** Implement `Boxes3D` and `Boxes2D` with aligned label, shape, and trajectory data, detached scalar conversion, and functional batch geometry. Build these directly from schema columns and relationship indexes. Add explicit batch APIs while preserving existing `get_box3d()` and list-returning `get_box3ds()` compatibility APIs; names in this document are provisional.
6. **Migrate expensive consumers to batch operations.** Move filtering, timeseries, box preparation, and viewer inputs to collection APIs, prioritizing measured bottlenecks. Avoid materializing all scalar boxes between stages. Compare batch geometry with the existing scalar implementation, including optional velocities, custom footprints, futures, and grouping by timestamp and frame.
7. **Review parity and switch defaults.** Run comparative benchmarks on representative large datasets, document API changes, and provide migration examples before changing the default or retiring the legacy backend.

## Acceptance criteria

- All columns stay aligned through construction and selection, including nullable and nested fields.
- Scalar records preserve values, types, and applicable derived shortcuts without sharing mutable storage.
- Normalized JSON exports match the existing backend, apart from explicitly documented changes.
- Lookup, relationship, timeseries, and geometry results remain equivalent, with defined floating-point tolerances where needed.
- Batch geometry preserves frame, rotation, size, corner, and trajectory conventions, leaves inputs unchanged, and handles empty collections and missing values.
- Box collections retain shared scalar timestamps and frame IDs through selection and scalar materialization, reject incompatible construction or concatenation, and update only the frame ID when changing coordinate frames.
- Bulk schema-to-box-to-viewer processing avoids constructing one scalar object per row except at explicit compatibility boundaries.
- Existing invalid inputs remain diagnosable, and intentional validation changes are documented.
- Benchmarks demonstrate useful memory and bulk-operation improvements; scalar-access regressions are measured and reviewed.

Choose numerical performance targets after measuring the baseline. Do not assume that replacing stored objects alone will accelerate consumers that still materialize and loop over every row.
