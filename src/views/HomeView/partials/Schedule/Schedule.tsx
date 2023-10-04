import { Table, Text } from '@radix-ui/themes';
import { format } from 'date-fns';

interface Game {
  datetime: string;
  location: string;
}

interface ScheduleProps {
  games: Game[];
}

const Schedule: React.FC<ScheduleProps> = ({ games }) => (
  <Table.Root variant="surface">
    <Table.Header>
      <Table.Row>
        <Table.ColumnHeaderCell>
          <Text weight="medium">Date & time</Text>
        </Table.ColumnHeaderCell>
        <Table.ColumnHeaderCell>
          <Text weight="medium">Location</Text>
        </Table.ColumnHeaderCell>
      </Table.Row>
    </Table.Header>

    <Table.Body>
      {games.map(({ datetime, location }) => (
        <Table.Row key={datetime}>
          <Table.Cell>
            <Text>{format(new Date(datetime), 'MM/dd/yyyy HH:mm')}</Text>
          </Table.Cell>
          <Table.Cell>
            <Text>{location}</Text>
          </Table.Cell>
        </Table.Row>
      ))}
    </Table.Body>
  </Table.Root>
);

export default Schedule;
