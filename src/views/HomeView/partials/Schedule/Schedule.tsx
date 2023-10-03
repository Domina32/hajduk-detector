import { Flex } from '@radix-ui/themes';
import { format } from 'date-fns';

interface Game {
  datetime: string;
  location: string;
}

interface ScheduleProps {
  games: Game[];
}

const Schedule: React.FC<ScheduleProps> = ({ games }) => (
  <Flex asChild direction="column" gap="5" grow="1">
    <ol>
      {games.map(({ datetime, location }) => (
        <Flex asChild key={datetime}>
          <li>
            {format(new Date(datetime), 'MM/dd/yyyy HH:mm')} at {location}
          </li>
        </Flex>
      ))}
    </ol>
  </Flex>
);

export default Schedule;
